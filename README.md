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
│   ├── app.py
│   └── api_client.py
├── .env.example
└── requirements.txt
```

## Backend setup

```bash
cd back
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt

cp ../.env.example ../.env  # optional: SMTP, SECRET_KEY, …

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

```bash
cd desktop
pip install -r requirements.txt
python app.py
```

Needs the backend running. Tabs: Login / Register / Profile / Data.

On Linux, if tkinter is missing: `sudo apt install python3-tk`

## Environment (`.env`)

Copy from `.env.example`. Important vars:

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `FRONTEND_URL` — link in password-reset emails
- `EMAIL_HOST` / `EMAIL_PORT` / … — leave empty to print mail to console
- `THROTTLE_PASSWORD_RESET` — default `5/hour`

## License

Private / educational project.
