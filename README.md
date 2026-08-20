# auth-api-tkinter

Django REST API (JWT auth) + **tkinter** desktop client.

Features:

- Register / Login (email) / Logout
- Profile (`GET`/`PATCH` me)
- Change password & password-reset (HTML email, rate-limited)
- Custom model **Notes** with search + pagination
- Desktop UI with form validation and non-blocking loading states
- Docker Compose (Django + Postgres) or local SQLite

> GitHub repo name: rename to **`auth-api-tkinter`** if you have not already  
> (Settings → General → Repository name)

---

## Structure

```
auth-api-tkinter/
├── back/                      # Django project
│   ├── authentication/        # auth endpoints + tests
│   ├── notes/                 # Note CRUD (search, pagination)
│   ├── users/                 # custom User (email + phone)
│   └── config/                # settings, urls
├── desktop/                   # tkinter client
│   ├── app.py
│   ├── api_client.py
│   └── requirements.txt
├── docker/
│   └── entrypoint.sh          # wait for DB → migrate → run
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── LICENSE                    # MIT
```

---

## Quick start (Docker)

```bash
git clone https://github.com/Atrasoufi/auth-api-tkinter.git
cd auth-api-tkinter

# optional: cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| API | http://127.0.0.1:8000/api/ |
| Health | http://127.0.0.1:8000/api/health/ |
| Postgres | `localhost:5432` |

Migrations run on container start.

```bash
docker compose logs -f web
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test authentication
docker compose down          # stop
docker compose down -v       # stop + wipe DB volume
```

---

## Backend without Docker

```bash
cd back
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt

cp ../.env.example ../.env   # leave POSTGRES_HOST empty → SQLite

python manage.py migrate
python manage.py test authentication
python manage.py runserver
```

---

## Desktop client

```bash
cd desktop
pip install -r requirements.txt
python app.py                # or python3 app.py
```

Requires the API at `http://127.0.0.1:8000/api`.

- **Login / Register** tabs (email login)
- After login: **Profile** + **Data** (notes)
- Client-side validation (email, password length, phone)
- Async requests so the UI does not freeze
- Notes: search, page prev/next

Linux: `sudo apt install python3-tk` if tkinter is missing.

---

## API reference

Base URL: `/api/`

### Auth

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| `POST` | `/auth/register/` | — | email, username, password, … |
| `POST` | `/auth/login/` | — | body: `email`, `password` → JWT |
| `POST` | `/auth/logout/` | JWT | blacklist refresh |
| `POST` | `/auth/token/refresh/` | — | |
| `GET` / `PATCH` | `/auth/me/` | JWT | profile |
| `POST` | `/auth/change-password/` | JWT | |
| `POST` | `/auth/password-reset/` | — | rate-limited |
| `POST` | `/auth/password-reset/confirm/` | — | |
| `GET` | `/health/` | — | |

Login field is **email** (`USERNAME_FIELD`).

### Notes (authenticated)

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/notes/?search=&page=&page_size=` | paginated list |
| `POST` | `/notes/` | create `{title, body}` |
| `GET` | `/notes/<id>/` | detail |
| `PATCH` | `/notes/<id>/` | update |
| `DELETE` | `/notes/<id>/` | delete |

Example list response:

```json
{
  "count": 42,
  "page": 1,
  "page_size": 10,
  "total_pages": 5,
  "results": [{ "id": 1, "title": "…", "body": "…", "created_at": "…", "updated_at": "…" }]
}
```

---

## Environment

Copy `.env.example` → `.env`:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | comma-separated |
| `CORS_ALLOWED_ORIGINS` | comma-separated |
| `FRONTEND_URL` | links in reset emails |
| `EMAIL_HOST` | empty → console backend |
| `THROTTLE_PASSWORD_RESET` | default `5/hour` |
| `POSTGRES_*` | used by Docker Compose |

---

## Stack

- Python 3.12+, Django 6, DRF, SimpleJWT
- Postgres 16 (Docker) or SQLite (local)
- tkinter + requests (desktop)

---

## License

[MIT](LICENSE) © 2026 Atrasoufi
