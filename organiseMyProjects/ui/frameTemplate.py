import tkinter as tk
from tkinter import ttk

from .baseFrame import BaseFrame


class FrameTemplate(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, title="Frame Template", actionButtonText="Run")

    def createMainArea(self):
        super().createMainArea()
        ttk.Label(self.frmMain, text="Main Area Content").pack(padx=10, pady=10)

    def onAction(self):
        self.statusField.show("Add your action handler here.")


def main():
    root = tk.Tk()
    root.withdraw()
    frame = FrameTemplate(root)
    frame.mainloop()


if __name__ == "__main__":
    main()
