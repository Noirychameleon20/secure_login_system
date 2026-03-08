"""
gui/dialogs.py  — Yellow cat-themed change password dialog
"""

import tkinter as tk
from core.auth_service import AuthService
from gui.styles import (COLORS, FONT_TITLE, FONT_SMALL,
                        styled_entry, styled_button,
                        ghost_button, section_label)


class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, master, auth: AuthService, username: str, on_done):
        super().__init__(master)
        self.auth     = auth
        self.username = username
        self.on_done  = on_done
        self.title("Change Password")
        self.configure(bg=COLORS["panel"])
        self.resizable(False, False)
        self._build()
        self.grab_set()

    def _build(self):
        pad = dict(pady=6, padx=36)

        tk.Label(self, text="( =\u03b5= )",
                 bg=COLORS["panel"], fg=COLORS["accent"],
                 font=("Courier New", 13, "bold")).pack(pady=(20, 2))
        tk.Label(self, text="\u2605 \u2605 \u2605",
                 bg=COLORS["panel"], fg=COLORS["accent2"],
                 font=("Georgia", 10)).pack(pady=(0, 4))

        tk.Label(self, text="\U0001f511 Change Password",
                 bg=COLORS["panel"], fg=COLORS["dark"],
                 font=FONT_TITLE).pack(pady=(0, 12))

        tk.Frame(self, bg=COLORS["accent2"], height=2,
                 width=260).pack(pady=(0, 10))

        for label, attr, show in [
            ("\U0001f512  current password", "entry_old",  "\u2022"),
            ("\u2728  new password",         "entry_new",  "\u2022"),
            ("\u2728  confirm new",          "entry_conf", "\u2022"),
        ]:
            section_label(self, f"  {label}").pack(anchor="w", padx=36)
            e = styled_entry(self, show=show, width=28)
            e.pack(**pad)
            setattr(self, attr, e)

        self.status = tk.Label(self, text="", bg=COLORS["panel"],
                               fg=COLORS["error"], font=FONT_SMALL,
                               wraplength=260)
        self.status.pack(pady=4)

        styled_button(self, "\U0001f43e  save changes",
                      self._save, width=26).pack(**pad)
        ghost_button(self, "cancel", self.destroy,
                     width=26).pack(pady=(0, 18))

    def _save(self):
        old  = self.entry_old.get()
        new  = self.entry_new.get()
        conf = self.entry_conf.get()
        if new != conf:
            self.status.config(text="passwords don't match \U0001f63f",
                               fg=COLORS["error"])
            return
        ok, msg = self.auth.change_password(self.username, old, new)
        if ok:
            self.status.config(text=msg, fg=COLORS["success"])
            self.after(1200, lambda: [self.destroy(), self.on_done()])
        else:
            self.status.config(text=msg, fg=COLORS["error"])
