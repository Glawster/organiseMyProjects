import tkinter as tk
from tkinter import ttk

from .statusFrame import StatusMessage
from .styleUtils import configureButtonStyle


class BaseFrame(tk.Toplevel):
    def __init__(self, parent, title="Base Frame", actionButtonText="Action"):
        super().__init__(parent)
        configureButtonStyle()
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.frmMain = ttk.Frame(self, padding=16)
        self.frmMain.pack(fill="both", expand=True)

        self.createMainArea()
        self.createButtonFrame(actionButtonText)

    def createMainArea(self):
        ttk.Label(self.frmMain, text="Override createMainArea() in your frame.").pack(
            padx=10,
            pady=10,
        )

    def createButtonFrame(self, actionButtonText):
        frmButtons = ttk.Frame(self.frmMain)
        frmButtons.pack(fill="x", pady=(12, 0))

        self.statusField = StatusMessage(frmButtons)
        self.statusField.frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(
            frmButtons,
            text=actionButtonText,
            style="primaryButton.TButton",
            command=self.onAction,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            frmButtons,
            text="Close",
            style="compactButton.TButton",
            command=self.destroy,
        ).pack(side=tk.LEFT)

    def onAction(self):
        self.statusField.show("Override onAction() in your frame.", success=False)
