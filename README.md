# scenario_django

Django REST API + tkinter desktop client for authentication.

## Structure

```
scenario_django/
├── back/                 # Django backend (API)
│   ├── authentication/   # register, login, logout, me, change/reset password
│   ├── users/            # custom User model (email login + phone)
│   └── config/           # settings, urls
├── desktop/              # tkinter desktop app
├── docker/
│   └── entrypoint.sh
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## Quick start with Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

- API: http://127.0.0.1:8000/api/
- Health: http://127.0.0.1:8000/api/health/
- Postgres on port `5432`

Migrations run automatically on container start.

Useful commands:

```bash
docker compose up --build -d      # background
docker compose logs -f web        # API logs
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test authentication
docker compose down               # stop
docker compose down -v            # stop + delete DB volume
```

## Backend without Docker

```bash
cd back
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt

cp ../.env.example ../.env
# leave POSTGRES_HOST empty → SQLite

python manage.py migrate
python manage.py test authentication
python manage.py runserver
```

API base: `http://127.0.0.1:8000/api/`

### Auth endpoints

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/api/auth/register/` | — |
| `POST` | `/api/auth/login/` | — (body: `email`, `password`) |
| `POST` | `/api/auth/logout/` | JWT |
| `POST` | `/api/auth/token/refresh/` | — |
| `GET` / `PATCH` | `/api/auth/me/` | JWT |
| `POST` | `/api/auth/change-password/` | JWT |
| `POST` | `/api/auth/password-reset/` | — |
| `POST` | `/api/auth/password-reset/confirm/` | — |
| `GET` | `/api/health/` | — |

Login uses **email** (`USERNAME_FIELD`).

## Desktop client

Runs on the host (not inside Docker):

```bash
cd desktop
pip install -r requirements.txt
python app.py
```

Needs the API at `http://127.0.0.1:8000/api` (Docker or local `runserver`).

On Linux: `sudo apt install python3-tk` if tkinter is missing.

## Environment (`.env`)

Copy from `.env.example`:

| Variable | Notes |
|----------|--------|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django core |
| `FRONTEND_URL` | Links in password-reset emails |
| `EMAIL_*` | Empty `EMAIL_HOST` → console backend |
| `THROTTLE_PASSWORD_RESET` | Default `5/hour` |
| `POSTGRES_*` | Used by Docker Compose |

## License

Private / educational project.
