"""
Desktop auth client (tkinter) for the Django scenario_django API.

Forms match the wireframe:
  Form 1 — Login / Register tabs
  Form 2 — Profile / Data tabs (after login)

Login uses email (USERNAME_FIELD on the backend).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from api_client import APIError, AuthAPI

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

BG = "#1a1b26"
CARD = "#24283b"
ACCENT = "#7aa2f7"
ACCENT_HOVER = "#89b4fa"
TEXT = "#c0caf5"
MUTED = "#565f89"
ENTRY_BG = "#1f2335"
DANGER = "#f7768e"
SUCCESS = "#9ece6a"

FONT = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_SMALL = ("Segoe UI", 9)


class AuthApp(tk.Tk):
    def __init__(self, api_base: str = "http://127.0.0.1:8000/api"):
        super().__init__()
        self.title("Auth Desktop")
        self.geometry("420x620")
        self.minsize(380, 560)
        self.configure(bg=BG)

        self.api = AuthAPI(base_url=api_base)
        self.current_user: dict | None = None

        self._setup_styles()
        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.show_auth()

    # ---- styles ----

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TNotebook",
            background=CARD,
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=ENTRY_BG,
            foreground=MUTED,
            padding=[16, 8],
            font=FONT_BOLD,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", CARD)],
            foreground=[("selected", ACCENT)],
        )

    # ---- helpers ----

    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def _card(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=CARD, padx=24, pady=20)
        f.pack(fill="both", expand=True)
        return f

    def _label(self, parent, text: str, **kw):
        return tk.Label(
            parent,
            text=text,
            bg=CARD,
            fg=TEXT,
            font=kw.pop("font", FONT),
            anchor="w",
            **kw,
        )

    def _entry(self, parent, show: str | None = None) -> tk.Entry:
        e = tk.Entry(
            parent,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
            highlightthickness=1,
            highlightbackground=MUTED,
            highlightcolor=ACCENT,
        )
        if show is not None:
            e.configure(show=show)
        e.pack(fill="x", ipady=8, pady=(2, 12))
        return e

    def _button(self, parent, text: str, command, primary: bool = True) -> tk.Button:
        bg = ACCENT if primary else ENTRY_BG
        fg = BG if primary else TEXT
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=ACCENT_HOVER if primary else MUTED,
            activeforeground=BG if primary else TEXT,
            relief="flat",
            font=FONT_BOLD,
            cursor="hand2",
            padx=16,
            pady=8,
        )
        btn.pack(fill="x", pady=(4, 8))
        return btn

    def _link(self, parent, text: str, command) -> tk.Label:
        lbl = tk.Label(
            parent,
            text=text,
            bg=CARD,
            fg=ACCENT,
            font=FONT_SMALL,
            cursor="hand2",
        )
        lbl.pack(pady=(0, 8))
        lbl.bind("<Button-1>", lambda _e: command())
        return lbl

    def _error(self, msg: str):
        messagebox.showerror("Error", msg, parent=self)

    def _info(self, msg: str):
        messagebox.showinfo("Info", msg, parent=self)

    def _ok(self, msg: str):
        messagebox.showinfo("Success", msg, parent=self)

    # ======================================================================
    # Form 1 — Auth (Login / Register)
    # ======================================================================

    def show_auth(self):
        self._clear()
        self.geometry("420x640")

        title = tk.Label(
            self.container,
            text="Welcome",
            bg=BG,
            fg=TEXT,
            font=FONT_TITLE,
        )
        title.pack(pady=(0, 12))

        card = self._card(self.container)
        nb = ttk.Notebook(card)
        nb.pack(fill="both", expand=True)

        login_tab = tk.Frame(nb, bg=CARD)
        register_tab = tk.Frame(nb, bg=CARD)
        nb.add(login_tab, text="  Login  ")
        nb.add(register_tab, text="  Register  ")

        self._build_login(login_tab)
        self._build_register(register_tab)

    def _build_login(self, parent):
        frame = tk.Frame(parent, bg=CARD, padx=8, pady=16)
        frame.pack(fill="both", expand=True)

        self._label(frame, "Email").pack(fill="x")
        email = self._entry(frame)

        self._label(frame, "Password").pack(fill="x")
        password = self._entry(frame, show="•")

        def do_login():
            e = email.get().strip()
            p = password.get()
            if not e or not p:
                self._error("Email and password are required.")
                return
            try:
                data = self.api.login(e, p)
                self.current_user = data.get("user") or self.api.me()
                self._ok("Logged in successfully.")
                self.show_main()
            except APIError as err:
                self._error(str(err))
            except requests_error():
                self._error("Cannot reach the server. Is runserver running?")

        self._button(frame, "Login", do_login)

        def do_forgot():
            e = email.get().strip()
            if not e:
                self._error("Enter your email first, then click Forgot password.")
                return
            try:
                res = self.api.password_reset_request(e)
                self._info(res.get("message", "Check your email / server console."))
            except APIError as err:
                self._error(str(err))
            except Exception:
                self._error("Cannot reach the server.")

        self._link(frame, "Forgot password?", do_forgot)

    def _build_register(self, parent):
        # scrollable for smaller screens
        canvas = tk.Canvas(parent, bg=CARD, highlightthickness=0)
        scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=CARD, padx=8, pady=12)

        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        fields = {}
        for key, label, show in [
            ("username", "Username", None),
            ("password", "Password", "•"),
            ("password_confirm", "Confirm password", "•"),
            ("email", "Email", None),
            ("first_name", "First name", None),
            ("last_name", "Last name", None),
            ("phone", "Phone", None),
        ]:
            self._label(frame, label).pack(fill="x")
            fields[key] = self._entry(frame, show=show)

        def do_register():
            data = {k: v.get().strip() if k != "password" and k != "password_confirm" else v.get()
                    for k, v in fields.items()}
            if not data["email"] or not data["username"] or not data["password"]:
                self._error("Email, username and password are required.")
                return
            if data["password"] != data["password_confirm"]:
                self._error("Passwords do not match.")
                return
            try:
                self.api.register(**data)
                self._ok("Registration successful. You can log in now.")
            except APIError as err:
                self._error(str(err))
            except Exception:
                self._error("Cannot reach the server.")

        self._button(frame, "Register", do_register)

    # ======================================================================
    # Form 2 — Main (Profile / Data)
    # ======================================================================

    def show_main(self):
        self._clear()
        self.geometry("440x580")

        header = tk.Frame(self.container, bg=BG)
        header.pack(fill="x", pady=(0, 12))

        user_label = self.current_user.get("email", "User") if self.current_user else "User"
        tk.Label(
            header,
            text=f"Hi, {user_label}",
            bg=BG,
            fg=TEXT,
            font=FONT_TITLE,
        ).pack(side="left")

        tk.Button(
            header,
            text="Logout",
            command=self._logout,
            bg=ENTRY_BG,
            fg=DANGER,
            relief="flat",
            font=FONT_SMALL,
            cursor="hand2",
            padx=10,
            pady=4,
        ).pack(side="right")

        card = self._card(self.container)
        nb = ttk.Notebook(card)
        nb.pack(fill="both", expand=True)

        profile_tab = tk.Frame(nb, bg=CARD)
        data_tab = tk.Frame(nb, bg=CARD)
        nb.add(profile_tab, text="  Profile  ")
        nb.add(data_tab, text="  Data  ")

        self._build_profile(profile_tab)
        self._build_data(data_tab)

    def _build_profile(self, parent):
        frame = tk.Frame(parent, bg=CARD, padx=8, pady=16)
        frame.pack(fill="both", expand=True)

        # load latest profile
        try:
            profile = self.api.me()
            self.current_user = profile
        except APIError:
            profile = self.current_user or {}

        fields = {}
        for key, label, show in [
            ("first_name", "First name", None),
            ("last_name", "Last name", None),
            ("phone", "Phone", None),
            ("old_password", "Current password", "•"),
            ("new_password", "New password", "•"),
            ("new_password_confirm", "Confirm new password", "•"),
        ]:
            self._label(frame, label).pack(fill="x")
            entry = self._entry(frame, show=show)
            if key in ("first_name", "last_name", "phone") and profile:
                entry.insert(0, profile.get(key, "") or "")
            fields[key] = entry

        def save_profile():
            try:
                updated = self.api.update_profile(
                    first_name=fields["first_name"].get().strip(),
                    last_name=fields["last_name"].get().strip(),
                    phone=fields["phone"].get().strip(),
                )
                self.current_user = updated
                self._ok("Profile updated.")
            except APIError as err:
                self._error(str(err))
            except Exception:
                self._error("Cannot reach the server.")

        def change_pass():
            old = fields["old_password"].get()
            new = fields["new_password"].get()
            conf = fields["new_password_confirm"].get()
            if not old or not new:
                self._error("Current and new password are required.")
                return
            if new != conf:
                self._error("New passwords do not match.")
                return
            try:
                self.api.change_password(old, new, conf)
                fields["old_password"].delete(0, "end")
                fields["new_password"].delete(0, "end")
                fields["new_password_confirm"].delete(0, "end")
                self._ok("Password changed.")
            except APIError as err:
                self._error(str(err))
            except Exception:
                self._error("Cannot reach the server.")

        self._button(frame, "Save profile", save_profile)
        self._button(frame, "Change password", change_pass, primary=False)

    def _build_data(self, parent):
        frame = tk.Frame(parent, bg=CARD, padx=16, pady=32)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Your custom model",
            bg=CARD,
            fg=MUTED,
            font=FONT_TITLE,
        ).pack(expand=True)

        tk.Label(
            frame,
            text="Placeholder for your business data.\nAdd models & endpoints later.",
            bg=CARD,
            fg=MUTED,
            font=FONT_SMALL,
            justify="center",
        ).pack()

    def _logout(self):
        try:
            self.api.logout()
        except Exception:
            pass
        self.current_user = None
        self.show_auth()


def requests_error():
    """Used in except clauses for network failures."""
    import requests

    return (requests.ConnectionError, requests.Timeout)


if __name__ == "__main__":
    # Change host/port if your Django server is elsewhere
    app = AuthApp(api_base="http://127.0.0.1:8000/api")
    app.mainloop()
