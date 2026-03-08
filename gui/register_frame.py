"""
gui/register_frame.py  — Yellow cat-themed registration screen
"""

import re
import tkinter as tk
from core.auth_service import AuthService
from gui.styles import (COLORS, FONT_TITLE, FONT_SMALL,
                        styled_entry, styled_button,
                        ghost_button, section_label)


class RegisterFrame(tk.Frame):
    def __init__(self, master, auth: AuthService, on_back, on_registered):
        super().__init__(master, bg=COLORS["bg"])
        self.auth          = auth
        self.on_back       = on_back
        self.on_registered = on_registered
        self._build()

    def _build(self):
        wrapper = tk.Frame(self, bg=COLORS["bg"])
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        outer = tk.Frame(wrapper, bg=COLORS["accent"], padx=3, pady=3)
        outer.pack()

        card = tk.Frame(outer, bg=COLORS["panel"], padx=44, pady=26)
        card.pack()

        tk.Label(card, text="( =^..^= )",
                 bg=COLORS["panel"], fg=COLORS["accent"],
                 font=("Courier New", 13, "bold")).pack(pady=(0, 2))

        tk.Label(card, text="\u2605 \u2605 \u2605",
                 bg=COLORS["panel"], fg=COLORS["accent2"],
                 font=("Georgia", 10)).pack(pady=(0, 4))

        tk.Label(card, text="Join the Cat Club!",
                 bg=COLORS["panel"], fg=COLORS["dark"],
                 font=FONT_TITLE).pack()
        tk.Label(card, text="create your cozy account \U0001f43e",
                 bg=COLORS["panel"], fg=COLORS["subtext"],
                 font=FONT_SMALL).pack(pady=(2, 12))

        tk.Frame(card, bg=COLORS["accent2"],
                 height=2, width=300).pack(pady=(0, 10))

        for label, attr, show in [
            ("\U0001f431  username",         "entry_user",  ""),
            ("\u2709\ufe0f  email",           "entry_email", ""),
            ("\U0001f511  password",          "entry_pass",  "\u2022"),
            ("\U0001f511  confirm password",  "entry_conf",  "\u2022"),
        ]:
            section_label(card, f"  {label}").pack(anchor="w")
            e = styled_entry(card, show=show, width=30)
            e.pack(pady=(3, 8))
            setattr(self, attr, e)

        self.strength_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self.strength_var,
                 bg=COLORS["panel"], fg=COLORS["subtext"],
                 font=FONT_SMALL).pack()
        self.entry_pass.bind("<KeyRelease>", self._check_strength)

        self.status = tk.Label(card, text="", bg=COLORS["panel"],
                               fg=COLORS["error"], font=FONT_SMALL,
                               wraplength=310)
        self.status.pack(pady=(4, 6))

        styled_button(card, "\U0001f43e  Create Account",
                      self._register, width=30).pack(pady=4)

        tk.Frame(card, bg=COLORS["accent2"],
                 height=2, width=300).pack(pady=(12, 8))

        ghost_button(card, "\u2190 back to login",
                     self.on_back, width=30).pack()

    def _check_strength(self, _=None):
        pw    = self.entry_pass.get()
        score = sum([
            len(pw) >= 8,
            bool(re.search(r"[A-Z]", pw)),
            bool(re.search(r"[a-z]", pw)),
            bool(re.search(r"\d", pw)),
            bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw)),
        ])
        labels = ["", "weak \U0001f534", "fair \U0001f7e0",
                  "okay \U0001f7e1", "good \U0001f7e2", "strong \U0001f63a"]
        self.strength_var.set(f"password strength: {labels[score]}" if pw else "")

    def _register(self):
        user  = self.entry_user.get().strip()
        email = self.entry_email.get().strip()
        pw    = self.entry_pass.get()
        conf  = self.entry_conf.get()
        if pw != conf:
            self.status.config(text="passwords don't match \U0001f63f",
                               fg=COLORS["error"])
            return
        ok, msg = self.auth.register(user, email, pw)
        if ok:
            self.status.config(text=msg, fg=COLORS["success"])
            self.after(1200, lambda: self.on_registered(user))
        else:
            self.status.config(text=msg, fg=COLORS["error"])

    def clear(self):
        for attr in ("entry_user", "entry_email", "entry_pass", "entry_conf"):
            getattr(self, attr).delete(0, "end")
        self.status.config(text="")
        self.strength_var.set("")
