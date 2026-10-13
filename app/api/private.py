"""Routeur privé : profil, accueil, discussions, projets et communauté.

Ce routeur sera monté avec la dépendance d'authentification obligatoire afin
que le sas d'entrée ne puisse pas être contourné par une route oubliée.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.domain import (
    Challenge,
    ChallengeSubmission,
    Comment,
    Conversation,
    ConversationMember,
    DeveloperProfile,
    Discussion,
    Match,
    MatchStatus,
    Message,
    Notification,
    Project,
    Resource,
    User,
)
from app.security import get_current_user

router = APIRouter(
    prefix="/api",
    tags=["private"],
    dependencies=[Depends(get_current_user)],
)


class ProfileUpdateRequest(BaseModel):
    """Champs éditables du profil développeur."""

    display_name: str = Field(min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    github_url: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=100)
    skills: list[str] = Field(default_factory=list, max_length=30)


class DiscussionRequest(BaseModel):
    """Contenu Markdown d'un sujet ou d'une réponse."""

    title: str = Field(min_length=3, max_length=200)
    body_markdown: str = Field(min_length=1, max_length=20000)


class CommentRequest(BaseModel):
    """Réponse Markdown facultativement rattachée à un commentaire parent."""

    body_markdown: str = Field(min_length=1, max_length=10000)
    parent_id: UUID | None = None


class ProjectRequest(BaseModel):
    """Données éditoriales d'un projet."""

    name: str = Field(min_length=1, max_length=150)
    description_markdown: str = Field(min_length=1, max_length=20000)
    repository_url: str | None = Field(default=None, max_length=255)
    demo_url: str | None = Field(default=None, max_length=255)


class ResourceRequest(BaseModel):
    """Lien partagé avec la communauté."""

    title: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=8, max_length=500)
    summary_markdown: str | None = Field(default=None, max_length=5000)


class ChallengeRequest(BaseModel):
    """Défi technique créé par un membre."""

    title: str = Field(min_length=1, max_length=200)
    description_markdown: str = Field(min_length=1, max_length=20000)
    deadline: datetime | None = None


class SubmissionRequest(BaseModel):
    """Dépôt d'une solution à un challenge."""

    repository_url: str = Field(min_length=8, max_length=255)
    note_markdown: str | None = Field(default=None, max_length=10000)


class MessageRequest(BaseModel):
    """Message privé adressé à un membre."""

    recipient_id: UUID
    body: str = Field(min_length=1, max_length=10000)


class MatchResponse(BaseModel):
    """Suggestion de mise en relation calculée depuis les compétences."""

    candidate_id: UUID
    username: str
    score: int
    status: MatchStatus


class CommunityMemberResponse(BaseModel):
    """Vue compacte d'un développeur dans l'annuaire."""

    user_id: UUID
    username: str
    display_name: str
    skills: list[str]
    github_url: str | None


@router.get("/profile")
async def read_profile(user: User = Depends(get_current_user)) -> dict[str, object]:
    """Retourne le profil du membre connecté."""
    profile = user.profile
    return {
        "username": user.username,
        "email": user.email,
        "display_name": profile.display_name if profile else user.username,
        "bio": profile.bio if profile else None,
        "github_url": profile.github_url if profile else None,
        "location": profile.location if profile else None,
        "skills": profile.skills if profile else [],
    }


@router.put("/profile")
async def update_profile(
    payload: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Met à jour le profil sans autoriser la modification du compte."""
    profile = user.profile
    if profile is None:
        profile = DeveloperProfile(user_id=user.id, display_name=payload.display_name)
        user.profile = profile
        db.add(profile)
    profile.display_name = payload.display_name
    profile.bio = payload.bio
    profile.github_url = payload.github_url
    profile.location = payload.location
    profile.skills = payload.skills
    await db.commit()
    return await read_profile(user)


@router.get("/dashboard")
async def dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Construit l'accueil avec contenu récent et compteurs du membre."""
    discussion_count = await db.scalar(
        select(func.count()).select_from(Discussion).where(Discussion.author_id == user.id)
    )
    project_count = await db.scalar(
        select(func.count()).select_from(Project).where(Project.owner_id == user.id)
    )
    notifications = (await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .order_by(Notification.id.desc())
        .limit(10)
    )).scalars().all()
    discussions = (await db.execute(
        select(Discussion).order_by(Discussion.created_at.desc()).limit(10)
    )).scalars().all()
    return {
        "user": user.username,
        "stats": {"discussions": discussion_count or 0, "projects": project_count or 0},
        "unread_notifications": notifications,
        "recent_discussions": discussions,
    }


@router.get("/community", response_model=list[CommunityMemberResponse])
async def search_community(
    query: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[CommunityMemberResponse]:
    """Recherche les profils actifs par nom d'utilisateur ou nom affiché."""
    statement = (
        select(User, DeveloperProfile)
        .join(DeveloperProfile, DeveloperProfile.user_id == User.id)
        .where(User.is_active.is_(True))
        .order_by(User.username)
        .limit(50)
    )
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            (User.username.ilike(pattern)) | (DeveloperProfile.display_name.ilike(pattern))
        )
    rows = (await db.execute(statement)).all()
    return [
        CommunityMemberResponse(
            user_id=user.id,
            username=user.username,
            display_name=profile.display_name,
            skills=profile.skills or [],
            github_url=profile.github_url,
        )
        for user, profile in rows
    ]


@router.post("/discussions", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_discussion(
    payload: DiscussionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Discussion:
    """Publie un sujet Markdown appartenant à l'auteur authentifié."""
    discussion = Discussion(author_id=user.id, title=payload.title, body_markdown=payload.body_markdown)
    db.add(discussion)
    await db.commit()
    await db.refresh(discussion)
    return discussion


@router.get("/discussions", response_model=None)
async def list_discussions(db: AsyncSession = Depends(get_db)) -> list[Discussion]:
    """Retourne les sujets récents sans charger inutilement leurs commentaires."""
    result = await db.execute(select(Discussion).order_by(Discussion.created_at.desc()).limit(50))
    return list(result.scalars())


@router.get("/messages", response_model=None)
async def list_messages(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Message]:
    """Retourne les messages envoyés ou reçus par le membre courant."""
    result = await db.execute(
        select(Message)
        .where((Message.sender_id == user.id) | (Message.recipient_id == user.id))
        .order_by(Message.sent_at.desc())
        .limit(50)
    )
    return list(result.scalars())


@router.post("/discussions/{discussion_id}/comments", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_comment(
    discussion_id: UUID,
    payload: CommentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Comment:
    """Ajoute une réponse à un sujet existant."""
    discussion = await db.get(Discussion, discussion_id)
    if discussion is None:
        raise HTTPException(status_code=404, detail="Discussion introuvable")
    comment = Comment(
        discussion_id=discussion_id,
        author_id=user.id,
        parent_id=payload.parent_id,
        body_markdown=payload.body_markdown,
    )
    db.add(comment)
    db.add(Notification(
        user_id=discussion.author_id,
        type="reply",
        title="Nouvelle réponse",
        body=f"{user.username} a répondu à votre discussion.",
    ))
    await db.commit()
    await db.refresh(comment)
    return comment


@router.post("/projects", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_project(
    payload: ProjectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Crée une fiche de projet appartenant au membre courant."""
    project = Project(owner_id=user.id, **payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/projects", response_model=None)
async def list_projects(db: AsyncSession = Depends(get_db)) -> list[Project]:
    """Liste les projets publiés, du plus récent au plus ancien."""
    result = await db.execute(select(Project).order_by(Project.created_at.desc()).limit(50))
    return list(result.scalars())


@router.post("/resources", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_resource(
    payload: ResourceRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Resource:
    """Partage un lien documenté en Markdown."""
    resource = Resource(author_id=user.id, **payload.model_dump())
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


@router.get("/resources", response_model=None)
async def list_resources(db: AsyncSession = Depends(get_db)) -> list[Resource]:
    """Retourne les ressources communautaires récentes."""
    result = await db.execute(select(Resource).order_by(Resource.created_at.desc()).limit(50))
    return list(result.scalars())


@router.post("/challenges", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_challenge(
    payload: ChallengeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Challenge:
    """Publie un challenge ou un hackathon."""
    challenge = Challenge(creator_id=user.id, **payload.model_dump())
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)
    return challenge


@router.post("/challenges/{challenge_id}/submissions", status_code=status.HTTP_201_CREATED, response_model=None)
async def submit_challenge(
    challenge_id: UUID,
    payload: SubmissionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChallengeSubmission:
    """Enregistre une soumission unique par utilisateur et challenge."""
    if await db.get(Challenge, challenge_id) is None:
        raise HTTPException(status_code=404, detail="Challenge introuvable")
    submission = ChallengeSubmission(challenge_id=challenge_id, user_id=user.id, **payload.model_dump())
    db.add(submission)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Vous avez déjà soumis ce challenge") from None
    await db.refresh(submission)
    return submission


@router.get("/matches", response_model=list[MatchResponse])
async def suggest_matches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MatchResponse]:
    """Calcule un score simple de complémentarité par intersection de skills."""
    profile = (await db.execute(
        select(DeveloperProfile).where(DeveloperProfile.user_id == user.id)
    )).scalar_one_or_none()
    own_skills = set(profile.skills if profile else [])
    candidates = (await db.execute(
        select(User, DeveloperProfile)
        .join(DeveloperProfile, DeveloperProfile.user_id == User.id)
        .where(User.id != user.id, User.is_active.is_(True))
        .limit(50)
    )).all()
    response: list[MatchResponse] = []
    for candidate, candidate_profile in candidates:
        score = len(own_skills.intersection(candidate_profile.skills or []))
        match = (await db.execute(select(Match).where(
            Match.requester_id == user.id, Match.candidate_id == candidate.id
        ))).scalar_one_or_none()
        if match is None:
            match = Match(
                requester_id=user.id,
                candidate_id=candidate.id,
                score=score,
                status=MatchStatus.PENDING,
            )
            db.add(match)
        else:
            match.score = score
        response.append(MatchResponse(
            candidate_id=candidate.id,
            username=candidate.username,
            score=score,
            status=match.status,
        ))
    await db.commit()
    return sorted(response, key=lambda item: item.score, reverse=True)


@router.post("/messages", status_code=status.HTTP_201_CREATED, response_model=None)
async def send_message(
    payload: MessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Message:
    """Crée une conversation directe si nécessaire puis envoie le message."""
    if payload.recipient_id == user.id or await db.get(User, payload.recipient_id) is None:
        raise HTTPException(status_code=404, detail="Destinataire introuvable")
    conversation = Conversation()
    db.add(conversation)
    await db.flush()
    db.add_all([
        ConversationMember(conversation_id=conversation.id, user_id=user.id),
        ConversationMember(conversation_id=conversation.id, user_id=payload.recipient_id),
    ])
    message = Message(
        conversation_id=conversation.id,
        sender_id=user.id,
        recipient_id=payload.recipient_id,
        body=payload.body,
    )
    db.add(message)
    db.add(Notification(
        user_id=payload.recipient_id,
        type="message",
        title="Nouveau message",
        body=f"{user.username} vous a envoyé un message.",
    ))
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/notifications", response_model=None)
async def list_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Notification]:
    """Retourne les alertes du membre courant."""
    result = await db.execute(select(Notification).where(
        Notification.user_id == user.id
    ).order_by(Notification.id.desc()).limit(50))
    return list(result.scalars())
