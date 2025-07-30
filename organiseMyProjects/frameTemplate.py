"""Generic Tkinter frame template."""

import tkinter as tk
from tkinter import ttk

from .styleUtils import configureButtonStyle


class ExampleFrame(ttk.Frame):
    """Example frame to base new frames on."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        configureButtonStyle()
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Example Frame").grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(
            self,
            text="Close",
            command=self.master.destroy,
            style="primaryButton.TButton",
        ).grid(row=1, column=0, pady=10)


def main():
    root = tk.Tk()
    root.title("Frame Template")
    frame = ExampleFrame(root)
    frame.pack(padx=20, pady=20)
    root.mainloop()


if __name__ == "__main__":
    main()
