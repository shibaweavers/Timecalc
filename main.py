#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk

from tkcalendar import Calendar

from themes import ThemeManager


class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Themed Calendar")

        # Create theme selector
        self.theme_var = tk.StringVar()
        self.theme_selector = ttk.Combobox(root,
                                           textvariable=self.theme_var,
                                           values=list(ThemeManager.THEMES.keys()))
        self.theme_selector.pack(pady=10)
        self.theme_selector.bind('<<ComboboxSelected>>', self.change_theme)

        # Create calendar
        self.calendar = Calendar(root)
        self.calendar.pack(pady=10, padx=10)

        # Apply initial theme
        self.change_theme(None)

    def change_theme(self, event):
        theme = self.theme_var.get()
        theme_colors = ThemeManager.THEMES[theme]()
        self.root.configure(bg=theme_colors['bg'])
        self.calendar.configure(
            background=theme_colors['bg'],
            foreground=theme_colors['fg'],
            selectbackground=theme_colors['entry_bg'],
            selectforeground=theme_colors['entry_fg']
        )


def main():
    root = tk.Tk()
    app = CalendarApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
