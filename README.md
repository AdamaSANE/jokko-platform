# JOKKO

Plateforme communautaire privée par et pour les développeurs — CADEV 2026.

> Auteur : Adama SANE - Développeur autodidacte en apprentissage continu, sans parcours académique technologique classique | GitHub : [https://github.com/AdamaSANE](https://github.com/AdamaSANE)

## Arborescence

```text
app/
  api/
    auth.py             # seules routes publiques : inscription/connexion
    exchanges.py        # code exchange, karma, leaderboard et portfolios
    password_reset.py   # récupération de mot de passe
    private.py          # sas commun à tous les modules connectés
  models/
    domain.py           # modèle PostgreSQL SQLAlchemy complet
  services/
    auth.py             # JWT, hachage et révocation
    exchanges.py        # résolution et attribution atomique des points d'impact
    matching.py         # JOKKO Match
  config.py             # variables d'environnement validées
  db.py                 # engine et sessions asynchrones
  security.py           # get_current_user, vérification JWT/session
  main.py               # composition de l'API
frontend/
  index.html            # ancien frontend conservé comme fallback
  styles.css            # styles du fallback
  app.js                # ancien client du fallback
frontend-react/
  public/jokko-mark.png  # logo officiel JOKKO sur fond transparent
  src/App.jsx           # composition du dashboard React
  src/api/              # client HTTP et appels vers FastAPI
  src/components/       # composants UI réutilisables
  src/main.jsx          # point d'entrée React
  src/styles.css        # interface responsive CADEV
migrations/             # versions Alembic
Dockerfile
docker-compose.yml
requirements.txt
```

## Sas d'entrée

`auth.router` et `password_reset.router` sont montés publiquement.
`private.router` porte `Depends(get_current_user)` au niveau du routeur :
toute nouvelle route ajoutée à ce routeur reste donc protégée par défaut.
La dépendance valide le JWT, son `jti`, l'existence de la session, son absence
de révocation et son expiration. La déconnexion peut ainsi invalider
immédiatement un token encore cryptographiquement valide.

## Couverture fonctionnelle du modèle

| Module | Tables principales |
|---|---|
| Authentification / déconnexion | `users`, `sessions` |
| Profil développeur | `developer_profiles`, `interests`, `user_interests` |
| Accueil personnalisé | `user_interests`, `follows`, contenu éditorial |
| Discussions Markdown | `discussions`, `comments`, `tags`, `discussion_tags` |
| Projets | `projects`, `project_collaborators`, `project_tags` |
| JOKKO Match | `matches` avec score, statut et contrainte d'unicité |
| Communauté | `users`, `developer_profiles`, `follows` |
| Ressources | `resources`, `resource_tags` |
| Challenges | `challenges`, `challenge_submissions` |
| Messages privés | `conversations`, `conversation_members`, `messages` |
| Notifications | `notifications` avec type, payload et lecture |
| Réactions | `likes` polymorphes, extensibles pour les contenus |

Les UUID évitent d'exposer des compteurs séquentiels. Les `ForeignKey` portent
`ON DELETE CASCADE` pour éviter les lignes orphelines, tandis que les tables
d'association explicites permettent d'ajouter des métadonnées et des index
sans dénormaliser les entités métier.

## API déjà fonctionnelle

| Méthode | Route | Accès |
|---|---|---|
| `POST` | `/auth/register` | Public |
| `POST` | `/auth/login` | Public |
| `POST` | `/auth/logout` | Bearer JWT |
| `GET` | `/auth/me` | Bearer JWT |
| `GET` | `/api/profile` | Bearer JWT |
| `PUT` | `/api/profile` | Bearer JWT |
| `POST/GET` | `/api/discussions` | Bearer JWT |
| `POST` | `/api/discussions/{id}/comments` | Bearer JWT |
| `POST/GET` | `/api/projects` | Bearer JWT |
| `POST/GET` | `/api/resources` | Bearer JWT |
| `POST` | `/api/challenges` | Bearer JWT |
| `POST` | `/api/challenges/{id}/submissions` | Bearer JWT |
| `GET` | `/api/matches` | Bearer JWT |
| `POST` | `/api/messages` | Bearer JWT |
| `GET` | `/api/notifications` | Bearer JWT |

| `GET` | `/api/dashboard` | Authentifié |
| `GET` | `/api/community?query=` | Authentifié |

Le mot de passe est haché avec bcrypt. Un JWT contient un identifiant unique
de session (`jti`) et sa validité dépend aussi de la ligne `sessions` en base.
Ainsi, un token volé peut être invalidé par la déconnexion.

## Code Exchange et preuve d'impact

La démo expose également une API versionnée, protégée par le même JWT :

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Créer un profil avec pays et stack technique |
| `GET/POST` | `/api/v1/exchanges/` | Lister ou publier un snippet, problème ou composant |
| `POST` | `/api/v1/exchanges/{id}/solutions` | Proposer une résolution par un pair |
| `PUT` | `/api/v1/exchanges/{id}/solve` | Valider une solution et attribuer 10 points |
| `GET` | `/api/v1/devs/leaderboard` | Classement par score d'impact |
| `GET` | `/api/v1/devs/portfolio/{id}` | Passeport technique public du développeur |

La validation est idempotence-protégée par le statut de l'échange : une demande
déjà résolue ne peut pas attribuer deux fois les points. Chaque attribution
est conservée dans `karma_events`, ce qui rend le score explicable. Les listes
ont une pagination bornée (`offset` et `limit`) et les réponses supérieures à
500 octets sont compressées avec Gzip pour les connexions à faible débit.

La marketplace expose aussi les composants techniques réutilisables :

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/api/v1/assets` | Lister les composants |
| `POST` | `/api/v1/assets` | Publier un composant |
| `POST` | `/api/v1/assets/{id}/download` | Enregistrer une utilisation |

## Démarrage local

Le parcours de référence pour le développement sur Windows utilise PostgreSQL
installé localement. Créer d'abord une base `jokko` et un utilisateur
`jokko`, puis copier `.env.example` vers `.env` et adapter les secrets.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH="C:\Users\LBC\Desktop\Hackathon"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

L'interface est disponible sur `http://localhost:8000/`. Docker Compose et
Codespaces restent disponibles pour un environnement isolé, mais ne sont pas
nécessaires pour le développement local Windows.

L'interface conserve uniquement le JWT de session dans le stockage local du
navigateur et revient au formulaire de connexion si le token est expiré ou
révoqué.

## Interface React

Une interface React/Vite complète est disponible dans `frontend-react/`. Elle
couvre la connexion, le tableau de bord, la publication d'échanges, les
solutions, le leaderboard, les portfolios, les messages et les notifications.
FastAPI reste le backend unique : React ne contient aucune logique métier et
communique uniquement avec les endpoints REST authentifiés.

Après un build React, FastAPI sert automatiquement `frontend-react/dist` sur
`http://localhost:8000/`. Le dossier `frontend/` n'est utilisé qu'en fallback
si le build React n'existe pas encore.

```powershell
cd frontend-react
npm install
npm run dev
```

Vite utilise un proxy vers FastAPI (`http://localhost:8000`). Le seeding de
démonstration ajoute précisément 8 messages et 9 notifications :

```powershell
cd ..
.\.venv\Scripts\python.exe -m app.seed
```

Pour afficher React via FastAPI directement :

```powershell
cd frontend-react
npm run build
cd ..
uvicorn app.main:app --reload
```

Ouvre ensuite `http://localhost:8000/`.

### Comptes de démonstration

Après le seeding, les comptes suivants utilisent le mot de passe
`Password123!` :

- `adama@jokko.sn`
- `awa@jokko.sn`
- `chinedu@jokko.ng`
