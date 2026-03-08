"""
gui/login_frame.py  — Yellow cat-themed login screen
"""

import tkinter as tk
from core.auth_service import AuthService
from gui.styles import (COLORS, FONT_TITLE, FONT_SMALL, FONT_BOLD,
                        styled_entry, styled_button,
                        ghost_button, section_label)

CAT_ART = "  /\\_/\\\n ( o.o )\n  > ^ <"


class LoginFrame(tk.Frame):
    def __init__(self, master, auth: AuthService, on_success, on_register):
        super().__init__(master, bg=COLORS["bg"])
        self.auth        = auth
        self.on_success  = on_success
        self.on_register = on_register
        self._build()

    def _build(self):
        wrapper = tk.Frame(self, bg=COLORS["bg"])
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        # outer glow border
        outer = tk.Frame(wrapper, bg=COLORS["accent"], padx=3, pady=3)
        outer.pack()

        card = tk.Frame(outer, bg=COLORS["panel"], padx=44, pady=32)
        card.pack()

        # ── cat art ──────────────────────────
        tk.Label(card, text=CAT_ART,
                 bg=COLORS["panel"], fg=COLORS["accent"],
                 font=("Courier New", 14, "bold"),
                 justify="center").pack(pady=(0, 2))

        # ── star row ─────────────────────────
        tk.Label(card, text="\u2605 \u2605 \u2605",
                 bg=COLORS["panel"], fg=COLORS["accent2"],
                 font=("Georgia", 10)).pack(pady=(0, 6))

        # ── title ────────────────────────────
        tk.Label(card, text="Welcome back!",
                 bg=COLORS["panel"], fg=COLORS["dark"],
                 font=FONT_TITLE).pack()
        tk.Label(card, text="your secure login portal  \U0001f511",
                 bg=COLORS["panel"], fg=COLORS["subtext"],
                 font=FONT_SMALL).pack(pady=(2, 16))

        # ── divider ──────────────────────────
        tk.Frame(card, bg=COLORS["accent2"],
                 height=2, width=300).pack(pady=(0, 14))

        # ── username ─────────────────────────
        section_label(card, "  \U0001f431  username").pack(anchor="w")
        self.entry_user = styled_entry(card, width=30)
        self.entry_user.pack(pady=(3, 10))

        # ── password ─────────────────────────
        section_label(card, "  \U0001f511  password").pack(anchor="w")
        self.entry_pass = styled_entry(card, show="\u2022", width=30)
        self.entry_pass.pack(pady=(3, 4))

        # ── show password ─────────────────────
        self.show_var = tk.BooleanVar()
        tk.Checkbutton(
            card, text="show password",
            variable=self.show_var, command=self._toggle_show,
            bg=COLORS["panel"], fg=COLORS["subtext"],
            selectcolor=COLORS["accent2"],
            activebackground=COLORS["panel"],
            font=FONT_SMALL, cursor="hand2", relief="flat", bd=0
        ).pack(anchor="w", pady=(0, 8))

        # ── status ────────────────────────────
        self.status = tk.Label(card, text="", bg=COLORS["panel"],
                               fg=COLORS["error"], font=FONT_SMALL,
                               wraplength=310)
        self.status.pack(pady=(0, 6))

        # ── login button ──────────────────────
        styled_button(card, "\U0001f43e  Login",
                      self._login, width=30).pack(pady=4)

        # ── divider ──────────────────────────
        tk.Frame(card, bg=COLORS["accent2"],
                 height=2, width=300).pack(pady=(14, 10))

        # ── register link ─────────────────────
        tk.Label(card, text="new here? join the cat club \U0001f63a",
                 bg=COLORS["panel"], fg=COLORS["subtext"],
                 font=FONT_SMALL).pack()
        ghost_button(card, "create an account",
                     self.on_register, width=30).pack(pady=(6, 0))

        self.entry_user.bind("<Return>", lambda _: self.entry_pass.focus())
        self.entry_pass.bind("<Return>", lambda _: self._login())

    def _toggle_show(self):
        self.entry_pass.config(show="" if self.show_var.get() else "\u2022")

    def _login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()
        if not username or not password:
            self.status.config(text="oops! fill in all fields \U0001f43e",
                               fg=COLORS["warning"])
            return
        ok, msg, token = self.auth.login(username, password)
        if ok:
            self.status.config(text=msg, fg=COLORS["success"])
            self.entry_pass.delete(0, "end")
            self.on_success(username, token)
        else:
            self.status.config(text=msg, fg=COLORS["error"])

    def clear(self):
        self.entry_user.delete(0, "end")
        self.entry_pass.delete(0, "end")
        self.status.config(text="")
