from tkinter import ttk

PRIMARY_COLOR = "#007BFF"
PRIMARY_HOVER = "#f0f8ff"
PRIMARY_PRESSED = "#0056b3"
BACKGROUND_COLOR = "white"


def configureButtonStyle():
    style = ttk.Style()

    style.configure("myEntry.TEntry", font=("Segoe UI", 10))
    style.configure(
        "primaryButton.TButton",
        foreground=PRIMARY_COLOR,
        background=BACKGROUND_COLOR,
        borderwidth=1,
        padding=(10, 6),
        width=25,
        relief="flat",
    )
    style.map(
        "primaryButton.TButton",
        background=[("active", PRIMARY_HOVER)],
        foreground=[("pressed", PRIMARY_PRESSED)],
    )

    style.configure(
        "compactButton.TButton",
        foreground=PRIMARY_COLOR,
        background=BACKGROUND_COLOR,
        borderwidth=1,
        padding=(5, 2),
        relief="flat",
    )
    style.map(
        "compactButton.TButton",
        background=[("active", PRIMARY_HOVER)],
        foreground=[("pressed", PRIMARY_PRESSED)],
    )
