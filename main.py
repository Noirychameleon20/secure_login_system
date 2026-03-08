"""
main.py  — Entry point. Wires core layer with GUI layer.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog

from core.database     import Database
from core.security     import SecurityManager
from core.auth_service import AuthService

from gui.login_frame     import LoginFrame
from gui.register_frame  import RegisterFrame
from gui.dashboard_frame import DashboardFrame
from gui.dialogs         import ChangePasswordDialog
from gui.styles          import COLORS


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SecurePaws \U0001f431 — ST5062CEM CW2")
        self.geometry("820x600")
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        self.db   = Database()
        self.sec  = SecurityManager()
        self.auth = AuthService(self.db, self.sec)

        self._current_frame = None
        self._show_login()

    def _clear(self):
        if self._current_frame:
            self._current_frame.pack_forget()

    def _show_login(self):
        self._clear()
        if not hasattr(self, "_login_frame"):
            self._login_frame = LoginFrame(
                self, auth=self.auth,
                on_success=self._on_login_success,
                on_register=self._show_register
            )
        self._login_frame.clear()
        self._login_frame.pack(fill="both", expand=True)
        self._current_frame = self._login_frame

    def _show_register(self):
        self._clear()
        if not hasattr(self, "_register_frame"):
            self._register_frame = RegisterFrame(
                self, auth=self.auth,
                on_back=self._show_login,
                on_registered=self._on_registered
            )
        self._register_frame.clear()
        self._register_frame.pack(fill="both", expand=True)
        self._current_frame = self._register_frame

    def _show_dashboard(self, username, token):
        self._clear()
        if not hasattr(self, "_dashboard_frame"):
            self._dashboard_frame = DashboardFrame(
                self, auth=self.auth, db=self.db,
                on_logout=self._on_logout,
                on_change_pw=self._on_change_pw,
                on_delete=self._on_delete
            )
        self._dashboard_frame.load(username, token)
        self._dashboard_frame.pack(fill="both", expand=True)
        self._current_frame = self._dashboard_frame

    def _on_login_success(self, username, token):
        self._show_dashboard(username, token)

    def _on_registered(self, username):
        messagebox.showinfo("Welcome!",
                            f"Account '{username}' created! \U0001f431 Please log in.")
        self._show_login()

    def _on_logout(self, token, username):
        self.auth.logout(token, username)
        self._show_login()

    def _on_change_pw(self, username):
        ChangePasswordDialog(self, self.auth, username,
                             on_done=self._show_login)

    def _on_delete(self, username, token):
        if not messagebox.askyesno("Delete Account",
                                   "Are you sure? This cannot be undone."):
            return
        pw = tkinter.simpledialog.askstring(
            "Confirm", "Enter your password:", show="*", parent=self)
        if pw is None:
            return
        ok, msg = self.auth.delete_account(username, pw)
        if ok:
            self.auth.logout(token, username)
            messagebox.showinfo("Deleted", msg)
            self._show_login()
        else:
            messagebox.showerror("Error", msg)


if __name__ == "__main__":
    app = App()
    app.mainloop()
