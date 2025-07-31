"""Example main menu for scaffolded projects."""

import tkinter as tk
from tkinter import ttk

from .styleUtils import configureButtonStyle


def mainMenu():
    
    root = tk.Tk()
    root.title("Main Menu")
    configureButtonStyle()
    ttk.Label(root, text="Main Menu").pack(padx=20, pady=10)
    ttk.Button(
        root,
        text="Exit",
        command=root.destroy,
        style="primaryButton.TButton",
    ).pack(pady=5)
    root.mainloop()


if __name__ == "__main__":
    mainMenu()
