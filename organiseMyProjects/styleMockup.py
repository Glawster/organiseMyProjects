"""Generate an SVG showing the shared Textual theme in ordinary use."""

from __future__ import annotations

import argparse
from pathlib import Path

from organiseMyProjects.version import VERSION

_THEME = Path(__file__).with_name("myStyles.css")
_PROJECT_THEME = Path("styles/projectStyles.css")


## command


def main(argv: list[str] | None = None) -> int:
    """Generate the shared Textual-style SVG and print its path."""
    parser = argparse.ArgumentParser(
        prog="styleMockup",
        description="Generate an SVG mockup of the shared Textual theme.",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    parser.parse_args(argv)
    try:
        output = styleMockupGenerate()
    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        if missing != "textual" and not missing.startswith("textual."):
            raise
        parser.error("styleMockup needs Textual; install organiseMyProjects[tui]")
    print(output)
    return 0


## mockup


def styleMockupGenerate() -> Path:
    """Render the effective shared or project-owned theme to its repository output."""
    root = repositoryRootFind(Path.cwd())
    stylesheet = styleSheetResolve(root)
    output = root / "output" / f"{stylesheet.stem}.svg"
    app = _mockupAppBuild(output, stylesheet)
    app.run(headless=True, size=(120, 42))
    if not output.is_file():
        raise RuntimeError(f"could not create SVG mockup at {output}")
    return output


def repositoryRootFind(start: Path) -> Path:
    """Return the nearest Git root, or the requested directory when outside Git."""
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def styleSheetResolve(root: Path) -> Path:
    """Return a project stylesheet override or OMP's canonical stylesheet."""
    candidate = root / _PROJECT_THEME
    return candidate if candidate.is_file() else _THEME


def _mockupAppBuild(output: Path, stylesheet: Path):
    """Build the optional Textual app only when SVG generation is requested."""
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import (
        Button,
        DataTable,
        Footer,
        Header,
        Input,
        Label,
        ListItem,
        ListView,
        Select,
        Static,
    )

    class StyleMockupApp(App):
        """Render representative controls against the canonical shared theme."""

        CSS_PATH = stylesheet

        def compose(self) -> ComposeResult:
            yield Header()
            with Vertical(id="style-mockup"):
                yield Static("Shared Textual styles", id="mockup-title")
                with Horizontal(classes="mockup-row"):
                    with Vertical(classes="surface mockup-panel"):
                        yield Label("List and states", classes="mockup-heading")
                        with ListView(id="mockup-list"):
                            yield ListItem(Label("Normal list item"))
                            yield ListItem(Label("Selected list item"))
                            yield ListItem(Label("Warning state", classes="warning"))
                    with Vertical(classes="surface mockup-panel"):
                        yield Label("Inputs and actions", classes="mockup-heading")
                        yield Input(placeholder="Search projects")
                        yield Select(
                            [("Development", "development"), ("Release", "release")],
                            prompt="Select branch type",
                        )
                        with Horizontal(classes="button-group"):
                            yield Button("Primary")
                            yield Button("Success", variant="success")
                        with Horizontal(classes="button-group"):
                            yield Button("Warning", variant="warning")
                            yield Button("Error", variant="error")
                    with Vertical(classes="surface mockup-panel"):
                        yield Label("Data table", classes="mockup-heading")
                        yield DataTable(id="mockup-table", cursor_type="row")
                with Horizontal(classes="mockup-row"):
                    yield Static(
                        "Success: validation passed",
                        classes="surface mockup-message success",
                    )
                    yield Static(
                        "Warning: review required",
                        classes="surface mockup-message warning",
                    )
                    yield Static(
                        "Error: action failed",
                        classes="surface mockup-message error",
                    )
            yield Footer()

        def on_mount(self) -> None:
            """Populate interactive examples, then export after the first layout."""
            listing = self.query_one("#mockup-list", ListView)
            listing.index = 1
            table = self.query_one("#mockup-table", DataTable)
            table.add_columns("Repository", "Branch", "Status")
            table.add_rows(
                [
                    ("organiseMyProjects", "feature/example", "InProgress"),
                    ("organiseMyPhotos", "main", "Completed"),
                ]
            )
            self.call_after_refresh(self._svgWrite)

        def _svgWrite(self) -> None:
            """Write the fully rendered screen and stop the headless app."""
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                self.export_screenshot(title="OMP shared Textual styles"),
                encoding="utf-8",
            )
            self.exit()

    return StyleMockupApp()


if __name__ == "__main__":
    raise SystemExit(main())
