import tkinter as tk


class StatusMessage:
    def __init__(
        self,
        parent,
        font=("Segoe UI", 10, "italic"),
        height=2,
        timeout=5000,
        wraplength=400,
    ):
        self.parent = parent
        self.frmStatus = tk.Frame(parent, highlightthickness=1)
        self.lblStatus = tk.Label(
            self.frmStatus,
            text="",
            anchor="center",
            font=font,
            height=height,
            wraplength=wraplength,
            justify="center",
        )
        self.lblStatus.pack(fill=tk.X)
        self.timeout = timeout

    def messageShow(self, message, success=True):
        color = "green" if success else "red"
        self.lblStatus.config(text=message, fg=color)
        self.frmStatus.config(highlightbackground=color, highlightcolor=color)
        self.frmStatus.after(self.timeout, self.messageClear)

    def messageClear(self):
        self.lblStatus.config(text="")
        bg = (
            self.parent.cget("bg") if "bg" in self.parent.keys() else "SystemButtonFace"
        )
        self.frmStatus.config(highlightbackground=bg, highlightcolor=bg)
