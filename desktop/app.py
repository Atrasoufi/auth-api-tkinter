"""
Desktop auth client (tkinter) for the Django scenario_django API.
"""

from __future__ import annotations

import re
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import requests

from api_client import APIError, AuthAPI

BG = "#1a1b26"
CARD = "#24283b"
ACCENT = "#7aa2f7"
ACCENT_HOVER = "#89b4fa"
TEXT = "#c0caf5"
MUTED = "#565f89"
ENTRY_BG = "#1f2335"
DANGER = "#f7768e"

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 15, "bold")
FONT_SMALL = ("Segoe UI", 9)

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^[+\d][\d\s\-]{6,20}$")


def valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value))


def valid_password(value: str) -> str | None:
    if len(value) < 8:
        return "Password must be at least 8 characters."
    return None


def valid_phone(value: str) -> bool:
    if not value:
        return True
    return bool(PHONE_RE.match(value))


class AuthApp(tk.Tk):
    def __init__(self, api_base: str = "http://127.0.0.1:8000/api"):
        super().__init__()
        self.title("Auth Desktop")
        self.geometry("400x720")
        self.minsize(360, 640)
        self.configure(bg=BG)

        self.api = AuthAPI(base_url=api_base)
        self.current_user: dict | None = None
        self._notes: list[dict] = []
        self._notes_page = 1
        self._notes_total_pages = 1
        self._notes_search = ""
        self._busy = False

        self._setup_styles()
        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True, padx=16, pady=16)

        self.status = tk.Label(
            self, text="", bg=BG, fg=MUTED, font=FONT_SMALL, anchor="w"
        )
        self.status.pack(fill="x", padx=16, pady=(0, 8))

        self.show_auth()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=CARD, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=ENTRY_BG,
            foreground=MUTED,
            padding=[14, 6],
            font=FONT_BOLD,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", CARD)],
            foreground=[("selected", ACCENT)],
        )

    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def _card(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=CARD, padx=16, pady=12)
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
        e.pack(fill="x", ipady=5, pady=(1, 6))
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
            padx=12,
            pady=6,
        )
        btn.pack(fill="x", pady=(2, 6))
        return btn

    def _link(self, parent, text: str, command) -> tk.Label:
        lbl = tk.Label(
            parent, text=text, bg=CARD, fg=ACCENT, font=FONT_SMALL, cursor="hand2"
        )
        lbl.pack(pady=(0, 6))
        lbl.bind("<Button-1>", lambda _e: command())
        return lbl

    def _set_status(self, text: str):
        self.status.configure(text=text)

    def _error(self, msg: str):
        self._set_status("")
        messagebox.showerror("Error", msg, parent=self)

    def _info(self, msg: str):
        self._set_status("")
        messagebox.showinfo("Info", msg, parent=self)

    def _ok(self, msg: str):
        self._set_status("")
        messagebox.showinfo("Success", msg, parent=self)

    def _run_async(self, work, on_ok=None, on_err=None, loading_msg: str = "Loading…"):
        """Run blocking API call off the UI thread; re-enable after."""
        if self._busy:
            return
        self._busy = True
        self._set_status(loading_msg)

        def worker():
            try:
                result = work()
            except Exception as exc:
                self.after(0, lambda: self._finish_async(err=exc, on_err=on_err))
            else:
                self.after(0, lambda: self._finish_async(result=result, on_ok=on_ok))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_async(self, result=None, err=None, on_ok=None, on_err=None):
        self._busy = False
        self._set_status("")
        if err is not None:
            if on_err:
                on_err(err)
            elif isinstance(err, APIError):
                self._error(str(err))
            elif isinstance(err, (requests.ConnectionError, requests.Timeout)):
                self._error("Cannot reach the server. Is runserver running?")
            else:
                self._error(str(err))
            return
        if on_ok:
            on_ok(result)

    # ---- Auth ----

    def show_auth(self):
        self._clear()
        self.geometry("400x720")

        tk.Label(
            self.container, text="Welcome", bg=BG, fg=TEXT, font=FONT_TITLE
        ).pack(pady=(0, 8))

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
        frame = tk.Frame(parent, bg=CARD, padx=8, pady=12)
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
            if not valid_email(e):
                self._error("Enter a valid email address.")
                return

            def work():
                return self.api.login(e, p)

            def ok(data):
                self.current_user = data.get("user") or self.api.me()
                self._ok("Logged in successfully.")
                self.show_main()

            self._run_async(work, on_ok=ok, loading_msg="Logging in…")

        self._button(frame, "Login", do_login)

        def do_forgot():
            e = email.get().strip()
            if not e:
                self._error("Enter your email first, then click Forgot password.")
                return
            if not valid_email(e):
                self._error("Enter a valid email address.")
                return

            def work():
                return self.api.password_reset_request(e)

            def ok(res):
                self._info(res.get("message", "Check your email / server console."))

            self._run_async(work, on_ok=ok, loading_msg="Sending reset email…")

        self._link(frame, "Forgot password?", do_forgot)

    def _build_register(self, parent):
        frame = tk.Frame(parent, bg=CARD, padx=8, pady=8)
        frame.pack(fill="both", expand=True)

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
            data = {
                k: v.get().strip()
                if k not in ("password", "password_confirm")
                else v.get()
                for k, v in fields.items()
            }
            if not data["username"]:
                self._error("Username is required.")
                return
            if len(data["username"]) < 3:
                self._error("Username must be at least 3 characters.")
                return
            if not data["email"] or not valid_email(data["email"]):
                self._error("Enter a valid email address.")
                return
            pwd_err = valid_password(data["password"])
            if pwd_err:
                self._error(pwd_err)
                return
            if data["password"] != data["password_confirm"]:
                self._error("Passwords do not match.")
                return
            if not valid_phone(data["phone"]):
                self._error("Phone looks invalid (use digits, optional +).")
                return

            def work():
                return self.api.register(**data)

            def ok(_):
                self._ok("Registration successful. You can log in now.")

            self._run_async(work, on_ok=ok, loading_msg="Registering…")

        self._button(frame, "Register", do_register)

    # ---- Main ----

    def show_main(self):
        self._clear()
        self.geometry("420x720")
        self._notes_page = 1
        self._notes_search = ""

        header = tk.Frame(self.container, bg=BG)
        header.pack(fill="x", pady=(0, 8))

        user_label = (
            self.current_user.get("email", "User") if self.current_user else "User"
        )
        tk.Label(
            header, text=f"Hi, {user_label}", bg=BG, fg=TEXT, font=FONT_TITLE
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
            padx=8,
            pady=3,
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
        frame = tk.Frame(parent, bg=CARD, padx=8, pady=8)
        frame.pack(fill="both", expand=True)

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
            phone = fields["phone"].get().strip()
            if not valid_phone(phone):
                self._error("Phone looks invalid (use digits, optional +).")
                return

            def work():
                return self.api.update_profile(
                    first_name=fields["first_name"].get().strip(),
                    last_name=fields["last_name"].get().strip(),
                    phone=phone,
                )

            def ok(updated):
                self.current_user = updated
                self._ok("Profile updated.")

            self._run_async(work, on_ok=ok, loading_msg="Saving profile…")

        def change_pass():
            old = fields["old_password"].get()
            new = fields["new_password"].get()
            conf = fields["new_password_confirm"].get()
            if not old or not new:
                self._error("Current and new password are required.")
                return
            pwd_err = valid_password(new)
            if pwd_err:
                self._error(pwd_err)
                return
            if new != conf:
                self._error("New passwords do not match.")
                return

            def work():
                return self.api.change_password(old, new, conf)

            def ok(_):
                for k in ("old_password", "new_password", "new_password_confirm"):
                    fields[k].delete(0, "end")
                self._ok("Password changed.")

            self._run_async(work, on_ok=ok, loading_msg="Changing password…")

        self._button(frame, "Save profile", save_profile)
        self._button(frame, "Change password", change_pass, primary=False)

    def _build_data(self, parent):
        frame = tk.Frame(parent, bg=CARD, padx=8, pady=8)
        frame.pack(fill="both", expand=True)

        self._label(frame, "My notes", font=FONT_BOLD).pack(fill="x")

        # search row
        search_row = tk.Frame(frame, bg=CARD)
        search_row.pack(fill="x", pady=(4, 4))

        search_entry = tk.Entry(
            search_row,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
            highlightthickness=1,
            highlightbackground=MUTED,
            highlightcolor=ACCENT,
        )
        search_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # list
        list_frame = tk.Frame(frame, bg=CARD)
        list_frame.pack(fill="both", expand=True, pady=(4, 4))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        notes_list = tk.Listbox(
            list_frame,
            bg=ENTRY_BG,
            fg=TEXT,
            selectbackground=ACCENT,
            selectforeground=BG,
            relief="flat",
            font=FONT,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
            height=5,
        )
        notes_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=notes_list.yview)
        self.notes_list = notes_list

        page_lbl = tk.Label(frame, text="", bg=CARD, fg=MUTED, font=FONT_SMALL)
        page_lbl.pack(fill="x")

        # form
        self._label(frame, "Title").pack(fill="x")
        title_entry = self._entry(frame)

        self._label(frame, "Body").pack(fill="x")
        body_entry = tk.Text(
            frame,
            height=2,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
            highlightthickness=1,
            highlightbackground=MUTED,
            highlightcolor=ACCENT,
        )
        body_entry.pack(fill="x", pady=(1, 6))

        def refresh_list():
            def work():
                return self.api.list_notes(
                    search=self._notes_search,
                    page=self._notes_page,
                    page_size=10,
                )

            def ok(payload):
                # support both old list and new paginated dict
                if isinstance(payload, list):
                    self._notes = payload
                    self._notes_total_pages = 1
                    count = len(payload)
                else:
                    self._notes = payload.get("results") or []
                    self._notes_page = payload.get("page", 1)
                    self._notes_total_pages = payload.get("total_pages", 1)
                    count = payload.get("count", 0)

                notes_list.delete(0, "end")
                for n in self._notes:
                    notes_list.insert("end", n.get("title", "(no title)"))
                page_lbl.configure(
                    text=f"Page {self._notes_page}/{self._notes_total_pages}  ·  {count} total"
                )

            self._run_async(work, on_ok=ok, loading_msg="Loading notes…")

        def do_search():
            self._notes_search = search_entry.get().strip()
            self._notes_page = 1
            refresh_list()

        def prev_page():
            if self._notes_page > 1:
                self._notes_page -= 1
                refresh_list()

        def next_page():
            if self._notes_page < self._notes_total_pages:
                self._notes_page += 1
                refresh_list()

        tk.Button(
            search_row,
            text="Search",
            command=do_search,
            bg=ACCENT,
            fg=BG,
            relief="flat",
            font=FONT_BOLD,
            cursor="hand2",
            padx=8,
            pady=3,
        ).pack(side="left", padx=(6, 0))

        nav = tk.Frame(frame, bg=CARD)
        nav.pack(fill="x", pady=(0, 4))
        tk.Button(
            nav,
            text="◀ Prev",
            command=prev_page,
            bg=ENTRY_BG,
            fg=TEXT,
            relief="flat",
            font=FONT_SMALL,
            cursor="hand2",
            padx=6,
        ).pack(side="left")
        tk.Button(
            nav,
            text="Next ▶",
            command=next_page,
            bg=ENTRY_BG,
            fg=TEXT,
            relief="flat",
            font=FONT_SMALL,
            cursor="hand2",
            padx=6,
        ).pack(side="left", padx=(6, 0))

        def on_select(_event=None):
            sel = notes_list.curselection()
            if not sel:
                return
            note = self._notes[sel[0]]
            title_entry.delete(0, "end")
            title_entry.insert(0, note.get("title", ""))
            body_entry.delete("1.0", "end")
            body_entry.insert("1.0", note.get("body", ""))

        notes_list.bind("<<ListboxSelect>>", on_select)

        def do_add():
            title = title_entry.get().strip()
            body = body_entry.get("1.0", "end").strip()
            if not title:
                self._error("Title is required.")
                return
            if len(title) > 200:
                self._error("Title max 200 characters.")
                return

            def work():
                return self.api.create_note(title, body)

            def ok(_):
                title_entry.delete(0, "end")
                body_entry.delete("1.0", "end")
                self._notes_page = 1
                refresh_list()

            self._run_async(work, on_ok=ok, loading_msg="Adding note…")

        def do_update():
            sel = notes_list.curselection()
            if not sel:
                self._error("Select a note first.")
                return
            note = self._notes[sel[0]]
            title = title_entry.get().strip()
            body = body_entry.get("1.0", "end").strip()
            if not title:
                self._error("Title is required.")
                return

            def work():
                return self.api.update_note(note["id"], title, body)

            def ok(_):
                self._ok("Note updated.")
                refresh_list()

            self._run_async(work, on_ok=ok, loading_msg="Updating…")

        def do_delete():
            sel = notes_list.curselection()
            if not sel:
                self._error("Select a note first.")
                return
            note = self._notes[sel[0]]
            if not messagebox.askyesno(
                "Delete", f"Delete «{note.get('title')}»?", parent=self
            ):
                return

            def work():
                return self.api.delete_note(note["id"])

            def ok(_):
                title_entry.delete(0, "end")
                body_entry.delete("1.0", "end")
                refresh_list()

            self._run_async(work, on_ok=ok, loading_msg="Deleting…")

        btn_row = tk.Frame(frame, bg=CARD)
        btn_row.pack(fill="x")

        for text, cmd, primary in [
            ("Add", do_add, True),
            ("Update", do_update, False),
            ("Delete", do_delete, False),
        ]:
            tk.Button(
                btn_row,
                text=text,
                command=cmd,
                bg=ACCENT if primary else ENTRY_BG,
                fg=BG if primary else TEXT,
                relief="flat",
                font=FONT_BOLD,
                cursor="hand2",
                padx=10,
                pady=5,
            ).pack(side="left", padx=(0, 6))

        search_entry.bind("<Return>", lambda _e: do_search())
        refresh_list()

    def _logout(self):
        try:
            self.api.logout()
        except Exception:
            pass
        self.current_user = None
        self.show_auth()


if __name__ == "__main__":
    app = AuthApp(api_base="http://127.0.0.1:8000/api")
    app.mainloop()
