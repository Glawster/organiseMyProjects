import tkinter as tk

from globalVars import PAD_X, PAD_Y, PAD_Y_TOP

class StatusMessage:
    
    def __init__(self, parent, font=("Segoe UI", 10, "italic"), height=2, timeout=5000, wraplength=400):

        self.parent = parent
        self.frame = tk.Frame(parent, highlightthickness=1)
        self.frame.pack(fill=tk.X, padx=PAD_X, pady=PAD_Y_TOP)

        self.label = tk.Label(
            self.frame,
            text="",
            anchor='center',
            font=font,
            height=height,
            wraplength=wraplength,
            justify="center"
        )
        self.label.pack(fill=tk.X)
        self.timeout = timeout

    def show(self, message, success = True):

        color = 'green' if success else 'red'
        self.label.config(text=message, fg=color)
        self.frame.config(
            highlightbackground=color,
            highlightcolor=color
        )
        self.frame.after(self.timeout, self.clear)

    def clear(self):
        
        self.label.config(text="")
        bg = self.parent.cget("bg") if "bg" in self.parent.keys() else "SystemButtonFace"
        self.frame.config(
            highlightbackground=bg,
            highlightcolor=bg
        )
