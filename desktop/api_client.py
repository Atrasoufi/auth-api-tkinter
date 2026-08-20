"""Thin HTTP client for the Django authentication + notes API."""

from __future__ import annotations

import requests


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, details=None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class AuthAPI:
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api"):
        self.base_url = base_url.rstrip("/")
        self.access: str | None = None
        self.refresh: str | None = None

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _headers(self, auth: bool = False) -> dict:
        headers = {"Content-Type": "application/json"}
        if auth and self.access:
            headers["Authorization"] = f"Bearer {self.access}"
        return headers

    def _handle(self, response: requests.Response):
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {"detail": response.text or "Unknown error"}

        if response.ok:
            return data

        if isinstance(data, dict):
            if "detail" in data:
                msg = str(data["detail"])
            else:
                parts = []
                for key, val in data.items():
                    if isinstance(val, list):
                        parts.append(f"{key}: {', '.join(str(v) for v in val)}")
                    else:
                        parts.append(f"{key}: {val}")
                msg = "\n".join(parts) if parts else "Request failed"
        else:
            msg = str(data)

        raise APIError(msg, status_code=response.status_code, details=data)

    # ---- auth ----

    def register(
        self,
        *,
        email: str,
        username: str,
        password: str,
        password_confirm: str,
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
    ) -> dict:
        payload = {
            "email": email,
            "username": username,
            "password": password,
            "password_confirm": password_confirm,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
        }
        r = requests.post(
            self._url("auth/register/"),
            json=payload,
            headers=self._headers(),
            timeout=15,
        )
        return self._handle(r)

    def login(self, email: str, password: str) -> dict:
        r = requests.post(
            self._url("auth/login/"),
            json={"email": email, "password": password},
            headers=self._headers(),
            timeout=15,
        )
        data = self._handle(r)
        self.access = data.get("access")
        self.refresh = data.get("refresh")
        return data

    def password_reset_request(self, email: str) -> dict:
        r = requests.post(
            self._url("auth/password-reset/"),
            json={"email": email},
            headers=self._headers(),
            timeout=15,
        )
        return self._handle(r)

    def me(self) -> dict:
        r = requests.get(
            self._url("auth/me/"),
            headers=self._headers(auth=True),
            timeout=15,
        )
        return self._handle(r)

    def update_profile(
        self,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
    ) -> dict:
        payload = {}
        if first_name is not None:
            payload["first_name"] = first_name
        if last_name is not None:
            payload["last_name"] = last_name
        if phone is not None:
            payload["phone"] = phone

        r = requests.patch(
            self._url("auth/me/"),
            json=payload,
            headers=self._headers(auth=True),
            timeout=15,
        )
        return self._handle(r)

    def change_password(
        self,
        old_password: str,
        new_password: str,
        new_password_confirm: str,
    ) -> dict:
        r = requests.post(
            self._url("auth/change-password/"),
            json={
                "old_password": old_password,
                "new_password": new_password,
                "new_password_confirm": new_password_confirm,
            },
            headers=self._headers(auth=True),
            timeout=15,
        )
        return self._handle(r)

    def logout(self) -> dict | None:
        if not self.refresh:
            self.access = None
            return None
        try:
            r = requests.post(
                self._url("auth/logout/"),
                json={"refresh": self.refresh},
                headers=self._headers(auth=True),
                timeout=15,
            )
            data = self._handle(r)
        except APIError:
            data = None
        finally:
            self.access = None
            self.refresh = None
        return data

    # ---- notes ----

    def list_notes(
        self,
        *,
        search: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        r = requests.get(
            self._url("notes/"),
            params=params,
            headers=self._headers(auth=True),
            timeout=15,
        )
        return self._handle(r)

    def create_note(self, title: str, body: str = "") -> dict:
        r = requests.post(
            self._url("notes/"),
            json={"title": title, "body": body},
            headers=self._headers(auth=True),
            timeout=15,
        )
        return self._handle(r)

    def update_note(self, note_id: int, title: str, body: str = "") -> dict:
        r = requests.patch(
            self._url(f"notes/{note_id}/"),
            json={"title": title, "body": body},
            headers=self._headers(auth=True),
            timeout=15,
        )
        return self._handle(r)

    def delete_note(self, note_id: int) -> None:
        r = requests.delete(
            self._url(f"notes/{note_id}/"),
            headers=self._headers(auth=True),
            timeout=15,
        )
        self._handle(r)
