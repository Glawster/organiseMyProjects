"""Project-neutral constants copied into newly scaffolded projects."""

APPLICATION = "Application"
DEBUG_MODE = False
PAD_X = 10
PAD_X_LEFT = (0, 5)
PAD_Y = 10
PAD_Y_TOP = (10, 0)
WINDOW_HEIGHT = 400
WINDOW_WIDTH = 600


def applicationTitleGet(subtitle: str | None = None) -> str:
    """Return the application title with an optional subtitle."""
    return f"{APPLICATION} — {subtitle}" if subtitle else APPLICATION


def debugModeIsEnabled() -> bool:
    """Return whether scaffold debugging is enabled."""
    return DEBUG_MODE
