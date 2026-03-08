"""
gui/dashboard_frame.py  — Yellow cat-themed dashboard
"""

import tkinter as tk
from tkinter import ttk
from core.database import Database
from core.auth_service import AuthService
from core.security import SecurityManager
from gui.styles import (COLORS, FONT_TITLE, FONT_HEADING, FONT_LABEL,
                        FONT_BOLD, FONT_SMALL, FONT_MONO,
                        styled_button, ghost_button, apply_treeview_style)


class DashboardFrame(tk.Frame):
    def __init__(self, master, auth: AuthService, db: Database,
                 on_logout, on_change_pw, on_delete):
        super().__init__(master, bg=COLORS["bg"])
        self.auth         = auth
        self.db           = db
        self.on_logout    = on_logout
        self.on_change_pw = on_change_pw
        self.on_delete    = on_delete
        self.username     = ""
        self.token        = ""
        self._build()

    def _build(self):
        apply_treeview_style()

        # ── Sidebar ──────────────────────────
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text=" /\\_/\\ \n( ^.^ )\n > \u2665 < ",
                 bg=COLORS["sidebar"], fg=COLORS["accent2"],
                 font=("Courier New", 11, "bold"),
                 justify="center").pack(pady=(20, 2))

        tk.Label(sidebar, text="SecurePaws",
                 bg=COLORS["sidebar"], fg="white",
                 font=FONT_HEADING).pack()

        self.user_badge = tk.Label(sidebar, text="",
                                   bg=COLORS["accent"],
                                   fg=COLORS["dark"],
                                   font=FONT_SMALL,
                                   padx=10, pady=3)
        self.user_badge.pack(pady=(8, 0), padx=14, fill="x")

        tk.Frame(sidebar, bg=COLORS["accent2"],
                 height=1).pack(fill="x", pady=10, padx=14)

        nav_items = [
            ("\U0001f3e0  home",              "_show_home"),
            ("\U0001f511  change password",   "_do_change_pw"),
            ("\U0001f4cb  audit logs",        "_show_logs"),
            ("\U0001f431  all users",         "_show_users"),
            ("\U0001f5d1\ufe0f  delete account", "_do_delete"),
        ]
        for label, method in nav_items:
            tk.Button(
                sidebar, text=label,
                bg=COLORS["sidebar"], fg="white",
                activebackground=COLORS["accent"],
                activeforeground=COLORS["dark"],
                relief="flat", anchor="w",
                padx=18, pady=9,
                font=FONT_LABEL, cursor="hand2",
                command=getattr(self, method)
            ).pack(fill="x", padx=6, pady=1)

        tk.Frame(sidebar, bg=COLORS["accent2"],
                 height=1).pack(fill="x", pady=10, padx=14)

        styled_button(sidebar, "logout", self._do_logout,
                      color=COLORS["accent"], width=16).pack(pady=8, padx=14)

        # ── Content ───────────────────────────
        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self._build_home()
        self._build_logs()
        self._build_users()
        self._show_home()

    # ── Build pages ──────────────────────────

    def _build_home(self):
        self.home_frame = tk.Frame(self.content, bg=COLORS["bg"])

        inner = tk.Frame(self.home_frame, bg=COLORS["bg"])
        inner.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(inner, text="\U0001f63a You're in!",
                 bg=COLORS["bg"], fg=COLORS["dark"],
                 font=FONT_TITLE).pack(pady=(0, 4))

        self.welcome_label = tk.Label(inner, text="",
                                      bg=COLORS["bg"],
                                      fg=COLORS["subtext"],
                                      font=FONT_SMALL)
        self.welcome_label.pack(pady=(0, 18))

        # info card
        card = tk.Frame(inner, bg=COLORS["panel"],
                        highlightthickness=2,
                        highlightbackground=COLORS["accent2"],
                        padx=24, pady=16)
        card.pack(fill="x", ipadx=10)

        tk.Label(card, text="\U0001f6e1\ufe0f  security details",
                 bg=COLORS["panel"], fg=COLORS["subtext"],
                 font=FONT_SMALL).pack(anchor="w", pady=(0, 8))

        for key, val in [
            ("algorithm",   "PBKDF2-HMAC-SHA256"),
            ("iterations",  f"{SecurityManager.ITERATIONS:,}"),
            ("salt",        "32 bytes (256-bit)"),
            ("session ttl", f"{SecurityManager.SESSION_TTL // 60} min"),
            ("lockout",     f"after {SecurityManager.MAX_ATTEMPTS} attempts"),
        ]:
            row = tk.Frame(card, bg=COLORS["panel"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=key, bg=COLORS["panel"],
                     fg=COLORS["subtext"], font=FONT_SMALL,
                     width=16, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=COLORS["panel"],
                     fg=COLORS["dark"], font=FONT_BOLD).pack(side="left")

        self.token_label = tk.Label(inner, text="",
                                    bg=COLORS["bg"],
                                    fg=COLORS["subtext"],
                                    font=FONT_MONO, wraplength=420)
        self.token_label.pack(pady=(10, 0))

    def _build_logs(self):
        self.logs_frame = tk.Frame(self.content, bg=COLORS["bg"])

        header = tk.Frame(self.logs_frame, bg=COLORS["bg"])
        header.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(header, text="\U0001f4cb  audit logs",
                 bg=COLORS["bg"], fg=COLORS["dark"],
                 font=FONT_TITLE).pack(side="left")
        ghost_button(header, "\u21bb refresh",
                     self._refresh_logs, width=10).pack(side="right")

        frame = tk.Frame(self.logs_frame, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=24, pady=4)

        cols   = ("timestamp", "user", "action", "status", "details")
        widths = [155, 90, 110, 75, 190]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=20)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

    def _build_users(self):
        self.users_frame = tk.Frame(self.content, bg=COLORS["bg"])

        header = tk.Frame(self.users_frame, bg=COLORS["bg"])
        header.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(header, text="\U0001f431  all users",
                 bg=COLORS["bg"], fg=COLORS["dark"],
                 font=FONT_TITLE).pack(side="left")
        ghost_button(header, "\u21bb refresh",
                     self._refresh_users, width=10).pack(side="right")

        frame = tk.Frame(self.users_frame, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=24, pady=4)

        cols   = ("id", "username", "email", "created", "locked", "fails")
        widths = [35, 110, 190, 150, 55, 55]
        self.utree = ttk.Treeview(frame, columns=cols, show="headings", height=20)
        for col, w in zip(cols, widths):
            self.utree.heading(col, text=col)
            self.utree.column(col, width=w, anchor="center")

        sb2 = ttk.Scrollbar(frame, orient="vertical", command=self.utree.yview)
        self.utree.configure(yscrollcommand=sb2.set)
        self.utree.pack(side="left", fill="both", expand=True)
        sb2.pack(side="left", fill="y")

    # ── Navigation ───────────────────────────

    def _hide_all(self):
        for f in (self.home_frame, self.logs_frame, self.users_frame):
            f.pack_forget()

    def _show_home(self):
        self._hide_all()
        self.home_frame.pack(fill="both", expand=True)

    def _show_logs(self):
        self._hide_all()
        self.logs_frame.pack(fill="both", expand=True)
        self._refresh_logs()

    def _show_users(self):
        self._hide_all()
        self.users_frame.pack(fill="both", expand=True)
        self._refresh_users()

    # ── Refresh ──────────────────────────────

    def _refresh_logs(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for log in self.db.get_audit_logs():
            tag = "ok" if log["status"] == "SUCCESS" else "bad"
            self.tree.insert("", "end", values=(
                log["timestamp"][:19], log["username"],
                log["action"], log["status"], log["details"]
            ), tags=(tag,))
        self.tree.tag_configure("ok",  foreground=COLORS["success"])
        self.tree.tag_configure("bad", foreground=COLORS["error"])

    def _refresh_users(self):
        for row in self.utree.get_children():
            self.utree.delete(row)
        for u in self.db.get_all_users():
            locked = "\U0001f512 yes" if u["is_locked"] else "\u2705 no"
            self.utree.insert("", "end", values=(
                u["id"], u["username"], u["email"],
                u["created_at"][:10], locked, u["failed_attempts"]
            ))

    # ── Actions ──────────────────────────────

    def _do_logout(self):    self.on_logout(self.token, self.username)
    def _do_change_pw(self): self.on_change_pw(self.username)
    def _do_delete(self):    self.on_delete(self.username, self.token)

    def load(self, username: str, token: str):
        self.username = username
        self.token    = token
        self.user_badge.config(text=f"\U0001f431  {username}")
        self.welcome_label.config(text=f"logged in as {username}  \U0001f43e")
        self.token_label.config(text=f"session: {token[:28]}\u2026")
