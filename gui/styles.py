"""
gui/styles.py
=============
Yellow cat-themed colour palette — warm yellow/gold/cream aesthetic.
"""

import tkinter as tk
from tkinter import ttk

COLORS = {
    "bg":        "#fffde7",   # soft yellow background
    "panel":     "#fff9c4",   # lighter yellow for panels/cards
    "card":      "#ffffff",
    "accent":    "#f9a825",   # golden yellow
    "accent2":   "#ffe082",   # pale gold
    "dark":      "#3e2723",   # dark brown text
    "text":      "#3e2723",
    "subtext":   "#795548",   # medium brown
    "success":   "#558b2f",   # earthy green
    "warning":   "#f57f17",   # amber
    "error":     "#bf360c",   # deep orange-red
    "entry_bg":  "#fffde7",   # same as bg for seamless look
    "border":    "#ffe082",   # gold border
    "highlight": "#f9a825",
    "sidebar":   "#f57f17",   # deep amber sidebar
    "sidebar_txt":"#fff8e1",
}

FONT_TITLE   = ("Georgia", 20, "bold")
FONT_HEADING = ("Georgia", 13, "bold")
FONT_LABEL   = ("Georgia", 10)
FONT_BOLD    = ("Georgia", 10, "bold")
FONT_SMALL   = ("Georgia", 9)
FONT_BUTTON  = ("Georgia", 10, "bold")
FONT_MONO    = ("Courier New", 8)


def styled_entry(parent, show="", width=26) -> tk.Entry:
    return tk.Entry(
        parent, show=show, width=width,
        bg=COLORS["entry_bg"],
        fg=COLORS["dark"],
        insertbackground=COLORS["accent"],
        relief="flat", font=FONT_LABEL,
        highlightthickness=2,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["accent"]
    )


def styled_button(parent, text, command,
                  color=None, width=22) -> tk.Button:
    bg = color or COLORS["accent"]
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=COLORS["dark"],
        activebackground=COLORS["dark"],
        activeforeground="white",
        relief="flat", font=FONT_BUTTON,
        width=width, pady=7, cursor="hand2", bd=0
    )


def ghost_button(parent, text, command, width=22) -> tk.Button:
    return tk.Button(
        parent, text=text, command=command,
        bg=COLORS["panel"], fg=COLORS["accent"],
        activebackground=COLORS["accent2"],
        activeforeground=COLORS["dark"],
        relief="flat", font=FONT_BUTTON,
        width=width, pady=7, cursor="hand2", bd=0
    )


def section_label(parent, text, bg=None) -> tk.Label:
    return tk.Label(
        parent, text=text,
        bg=bg or COLORS["panel"],
        fg=COLORS["subtext"],
        font=FONT_SMALL
    )


def apply_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                    background=COLORS["card"],
                    foreground=COLORS["dark"],
                    rowheight=28,
                    fieldbackground=COLORS["card"],
                    font=FONT_SMALL, borderwidth=0)
    style.configure("Treeview.Heading",
                    background=COLORS["accent2"],
                    foreground=COLORS["dark"],
                    font=FONT_BOLD, relief="flat")
    style.map("Treeview",
              background=[("selected", COLORS["accent"])],
              foreground=[("selected", COLORS["dark"])])
