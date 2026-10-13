# Auteur : Adama SANE - Développeur autodidacte en apprentissage continu, sans parcours académique technologique classique | GitHub : [https://github.com/AdamaSANE](https://github.com/AdamaSANE)
"""Modèle relationnel complet du domaine JOKKO.

Les tables d'association sont explicites plutôt que cachées dans des listes :
elles permettent d'ajouter des métadonnées (rôle, date, statut) et rendent les
requêtes PostgreSQL et leur explication au jury transparentes.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base commune permettant à Alembic d'introspecter tous les modèles."""


class TimestampMixin:
    """Colonnes temporelles partagées par les entités éditables."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MatchStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class ExchangeStatus(str, Enum):
    OPEN = "open"
    SOLVED = "solved"


class ExchangeKind(str, Enum):
    SNIPPET = "snippet"
    PROBLEM = "problem"
    COMPONENT = "component"


class AssetKind(str, Enum):
    SCRIPT = "script"
    MIDDLEWARE = "middleware"
    DOCKER = "docker"
    MOBILE_MONEY = "mobile_money"
    USSD = "ussd"


class NotificationType(str, Enum):
    MATCH = "match"
    REPLY = "reply"
    MESSAGE = "message"
    SYSTEM = "system"


class User(Base, TimestampMixin):
    """Compte authentifiable : un utilisateur possède un profil développeur."""

    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    profile: Mapped["DeveloperProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    discussions: Mapped[list["Discussion"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    resources: Mapped[list["Resource"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sent_messages: Mapped[list["Message"]] = relationship(foreign_keys="Message.sender_id", back_populates="sender")
    received_messages: Mapped[list["Message"]] = relationship(foreign_keys="Message.recipient_id", back_populates="recipient")
    exchanges: Mapped[list["Exchange"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    solutions: Mapped[list["ExchangeSolution"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    karma_events: Mapped[list["KarmaEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    assets: Mapped[list["Asset"]] = relationship(back_populates="author", cascade="all, delete-orphan")


class DeveloperProfile(Base, TimestampMixin):
    """Profil public : bio, stack et lien GitHub pour l'annuaire et le matching."""

    __tablename__ = "developer_profiles"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    github_url: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(100))
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    impact_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    user: Mapped["User"] = relationship(back_populates="profile")


class Session(Base):
    """Session révocable : la déconnexion invalide le JWT via ``revoked_at``."""

    __tablename__ = "sessions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    user: Mapped["User"] = relationship(back_populates="sessions")


class Interest(Base):
    """Centre d'intérêt utilisé pour personnaliser le tableau de bord."""

    __tablename__ = "interests"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    users: Mapped[list["UserInterest"]] = relationship(back_populates="interest", cascade="all, delete-orphan")


class UserInterest(Base):
    """Association utilisateur-intérêt, pondérée pour le feed personnalisé."""

    __tablename__ = "user_interests"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    interest_id: Mapped[UUID] = mapped_column(ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer, default=1)
    interest: Mapped["Interest"] = relationship(back_populates="users")


class Tag(Base):
    """Tag réutilisable pour discussions, projets et ressources."""

    __tablename__ = "tags"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)


class Discussion(Base, TimestampMixin):
    """Sujet de forum orienté code, dont le corps conserve le Markdown brut."""

    __tablename__ = "discussions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body_markdown: Mapped[str] = mapped_column(Text)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    author: Mapped["User"] = relationship(back_populates="discussions")
    comments: Mapped[list["Comment"]] = relationship(back_populates="discussion", cascade="all, delete-orphan")
    tags: Mapped[list["DiscussionTag"]] = relationship(cascade="all, delete-orphan")


class DiscussionTag(Base):
    """Association normalisée entre un sujet et ses tags."""

    __tablename__ = "discussion_tags"
    discussion_id: Mapped[UUID] = mapped_column(ForeignKey("discussions.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Comment(Base, TimestampMixin):
    """Réponse à une discussion, avec support de fils via ``parent_id``."""

    __tablename__ = "comments"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    discussion_id: Mapped[UUID] = mapped_column(ForeignKey("discussions.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))
    body_markdown: Mapped[str] = mapped_column(Text)
    discussion: Mapped["Discussion"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")


class Project(Base, TimestampMixin):
    """Projet personnel ou open source présenté par son propriétaire."""

    __tablename__ = "projects"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    description_markdown: Mapped[str] = mapped_column(Text)
    repository_url: Mapped[Optional[str]] = mapped_column(String(255))
    demo_url: Mapped[Optional[str]] = mapped_column(String(255))
    owner: Mapped["User"] = relationship(back_populates="projects")
    collaborators: Mapped[list["ProjectCollaborator"]] = relationship(cascade="all, delete-orphan")
    tags: Mapped[list["ProjectTag"]] = relationship(cascade="all, delete-orphan")


class ProjectCollaborator(Base):
    """Partenaire de projet avec rôle explicite pour la page de documentation."""

    __tablename__ = "project_collaborators"
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(80), default="contributor")


class ProjectTag(Base):
    """Association projet-tag."""

    __tablename__ = "project_tags"
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Match(Base, TimestampMixin):
    """Suggestion de JOKKO Match entre deux profils complémentaires."""

    __tablename__ = "matches"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    candidate_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer)
    status: Mapped[MatchStatus] = mapped_column(SAEnum(MatchStatus), default=MatchStatus.PENDING)
    __table_args__ = (UniqueConstraint("requester_id", "candidate_id"), Index("ix_matches_candidate", "candidate_id"))


class Follow(Base):
    """Abonnement entre membres pour alimenter l'accueil personnalisé."""

    __tablename__ = "follows"
    follower_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    followed_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class Resource(Base, TimestampMixin):
    """Lien, tutoriel ou astuce partagé avec la communauté."""

    __tablename__ = "resources"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(500))
    summary_markdown: Mapped[Optional[str]] = mapped_column(Text)
    author: Mapped["User"] = relationship(back_populates="resources")
    tags: Mapped[list["ResourceTag"]] = relationship(cascade="all, delete-orphan")


class ResourceTag(Base):
    """Association ressource-tag."""

    __tablename__ = "resource_tags"
    resource_id: Mapped[UUID] = mapped_column(ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Challenge(Base, TimestampMixin):
    """Défi technique ou hackathon publié par la communauté."""

    __tablename__ = "challenges"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    description_markdown: Mapped[str] = mapped_column(Text)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    submissions: Mapped[list["ChallengeSubmission"]] = relationship(cascade="all, delete-orphan")


class ChallengeSubmission(Base, TimestampMixin):
    """Soumission d'un utilisateur à un challenge."""

    __tablename__ = "challenge_submissions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    challenge_id: Mapped[UUID] = mapped_column(ForeignKey("challenges.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    repository_url: Mapped[str] = mapped_column(String(255))
    note_markdown: Mapped[Optional[str]] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("challenge_id", "user_id"),)


class Conversation(Base, TimestampMixin):
    """Conversation privée, indépendante des messages individuels."""

    __tablename__ = "conversations"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    members: Mapped[list["ConversationMember"]] = relationship(cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class ConversationMember(Base):
    """Membre d'une conversation privée."""

    __tablename__ = "conversation_members"
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class Message(Base):
    """Message privé adressé à un membre, traçable et marqué comme lu."""

    __tablename__ = "messages"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    recipient_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id], back_populates="sent_messages")
    recipient: Mapped["User"] = relationship(foreign_keys=[recipient_id], back_populates="received_messages")


class Notification(Base):
    """Alerte persistée pour matchs, réponses et messages."""

    __tablename__ = "notifications"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    payload: Mapped[Optional[str]] = mapped_column(Text)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    user: Mapped["User"] = relationship(back_populates="notifications")


class Exchange(Base, TimestampMixin):
    """Demande d'entraide, snippet ou composant réutilisable."""

    __tablename__ = "exchanges"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    code: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(String(50))
    kind: Mapped[ExchangeKind] = mapped_column(SAEnum(ExchangeKind), default=ExchangeKind.PROBLEM)
    status: Mapped[ExchangeStatus] = mapped_column(SAEnum(ExchangeStatus), default=ExchangeStatus.OPEN)
    author: Mapped["User"] = relationship(back_populates="exchanges")
    solutions: Mapped[list["ExchangeSolution"]] = relationship(
        back_populates="exchange", cascade="all, delete-orphan"
    )


class ExchangeSolution(Base, TimestampMixin):
    """Proposition d'un pair pour résoudre un échange."""

    __tablename__ = "exchange_solutions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    exchange_id: Mapped[UUID] = mapped_column(ForeignKey("exchanges.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exchange: Mapped["Exchange"] = relationship(back_populates="solutions")
    author: Mapped["User"] = relationship(back_populates="solutions")


class KarmaEvent(Base):
    """Événement immuable expliquant l'évolution d'un score d'impact."""

    __tablename__ = "karma_events"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exchange_id: Mapped[UUID] = mapped_column(ForeignKey("exchanges.id", ondelete="CASCADE"), index=True)
    points: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(200))
    user: Mapped["User"] = relationship(back_populates="karma_events")


class Asset(Base, TimestampMixin):
    """Composant technique réutilisable publié dans la marketplace."""

    __tablename__ = "assets"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500))
    kind: Mapped[AssetKind] = mapped_column(SAEnum(AssetKind))
    language: Mapped[Optional[str]] = mapped_column(String(50))
    license: Mapped[str] = mapped_column(String(80), default="MIT")
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    author: Mapped["User"] = relationship(back_populates="assets")


class Like(Base):
    """Réaction polymorphe réservée à une future couche de modération."""

    __tablename__ = "likes"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    target_type: Mapped[str] = mapped_column(String(30), primary_key=True)
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
