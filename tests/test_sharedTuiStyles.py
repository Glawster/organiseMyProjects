"""Shared theme deployment and real Textual layout regressions."""

import asyncio
import importlib.util
from pathlib import Path
import re

import pytest

from organiseMyProjects import manageProject
from organiseMyProjects.managedContent import managedContentBody, managedContentBuild

THEME = Path(manageProject.TEMPLATE_DIR) / "myStyles.css"
REQUIRES_TEXTUAL = pytest.mark.skipif(
    importlib.util.find_spec("textual") is None,
    reason="textual is not installed; run in the ompr Conda environment",
)


def testThemePaletteUsesVariables():
    text = THEME.read_text()
    tokenBlock, rules = text.split("/* Shared OMP application theme.", 1)
    tokens = re.findall(r"^\$[\w-]+: #[0-9a-f]{6};$", tokenBlock, re.MULTILINE)
    assert len(tokens) == 24
    assert re.search(r"#[0-9a-f]{6}", rules) is None
    assert "background: $surface;" in rules
    assert rules.count("border: solid $success-text;") == 3


def testStylesDeployment(tmp_path):
    project = tmp_path / "tuiProject"
    manageProject.createProject(project)
    deployed = project / "myStyles.css"
    assert managedContentBody(deployed.read_text())[0] == THEME.read_text()
    deployed.write_text(managedContentBuild("/* obsolete */", ".css"))
    before = deployed.read_bytes()
    manageProject.updateProject(project, dryRun=True)
    assert deployed.read_bytes() == before
    manageProject.updateProject(project)
    assert managedContentBody(deployed.read_text())[0] == THEME.read_text()
    before = deployed.stat().st_mtime_ns
    manageProject.updateProject(project)
    assert deployed.stat().st_mtime_ns == before


@REQUIRES_TEXTUAL
def testSharedScrollbarContrast():
    from textual.app import App, ComposeResult
    from textual.widgets import DataTable, Input, Select

    class ThemeApp(App):
        CSS_PATH = THEME

        def compose(self) -> ComposeResult:
            yield DataTable(id="table")
            yield Input(id="input")
            yield Select([("Development", "development")], id="select")

    async def verify():
        async with ThemeApp().run_test() as pilot:
            pilot.app.set_focus(None)
            await pilot.pause()
            styles = pilot.app.query_one("#table", DataTable).styles
            for selector in ("#table", "#input", "#select"):
                border = pilot.app.query_one(selector).styles.border[0][1]
                assert (border.r, border.g, border.b) == (117, 224, 191)
            assert (
                styles.scrollbar_background.r,
                styles.scrollbar_background.g,
                styles.scrollbar_background.b,
            ) == (16, 31, 46)
            assert (
                styles.scrollbar_color.r,
                styles.scrollbar_color.g,
                styles.scrollbar_color.b,
            ) == (96, 120, 142)
            assert (
                styles.scrollbar_color_hover.r,
                styles.scrollbar_color_hover.g,
                styles.scrollbar_color_hover.b,
            ) == (143, 163, 184)
            assert (
                styles.scrollbar_color_active.r,
                styles.scrollbar_color_active.g,
                styles.scrollbar_color_active.b,
            ) == (217, 229, 239)

    asyncio.run(verify())


@pytest.mark.parametrize("name", ["customProject", "clannEolas"])
def testProjectOwnedStylesPreserved(tmp_path, name):
    project = tmp_path / name
    project.mkdir()
    stylesheet = project / "myStyles.css"
    stylesheet.write_text("/* application-owned */")
    manageProject.updateProject(project)
    assert stylesheet.read_text() == "/* application-owned */"


@REQUIRES_TEXTUAL
@pytest.mark.parametrize("size", [(81, 24), (41, 16), (80, 24), (40, 16)])
def testRenderedButtonGroup(size):
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal
    from textual.widgets import Button

    class ThemeApp(App):
        CSS_PATH = THEME

        def compose(self) -> ComposeResult:
            with Horizontal(classes="button-group"):
                yield Button("Run", id="run")
                yield Button("Cancel", variant="error", id="cancel")

    async def verify():
        app = ThemeApp()
        async with app.run_test(size=size) as pilot:
            buttons = list(app.query(Button))
            group = app.query_one(".button-group")
            for button in buttons:
                assert button.region.height == 1
                assert button.content_region.height == 1
                assert button.styles.padding.top == button.styles.padding.bottom == 0
                assert button.render().plain.strip() == str(button.label)
            assert abs(buttons[0].region.width - buttons[1].region.width) <= 1
            assert buttons[1].region.x - buttons[0].region.right == 1
            assert group.styles.margin.top == group.styles.margin.bottom == 1
            for button in buttons:
                button.focus()
                await pilot.hover(f"#{button.id}")
                await pilot.pause()
                assert button.content_region.height == 1
                button.add_class("-active")
                await pilot.pause()
                assert button.content_region.height == 1
                button.disabled = True
                await pilot.pause()
                assert button.content_region.height == 1

    asyncio.run(verify())


@REQUIRES_TEXTUAL
@pytest.mark.parametrize("size", [(80, 24), (40, 16)])
def testPlainHorizontalButtonGaps(size):
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal
    from textual.widgets import Button

    class ThemeApp(App):
        CSS_PATH = THEME
        CSS = "Horizontal > Button { width: 1fr; min-width: 0; }"

        def compose(self) -> ComposeResult:
            # Match existing execution screens that do not opt into a class.
            with Horizontal():
                yield Button("Refresh")
                yield Button("Selected")
                yield Button("All")

    async def verify():
        async with ThemeApp().run_test(size=size) as pilot:
            buttons = list(pilot.app.query(Button))
            for left, right in zip(buttons, buttons[1:]):
                assert right.region.x - left.region.right == 1
            assert buttons[-1].styles.margin.right == 0
            assert all(button.content_region.height == 1 for button in buttons)
            widths = [button.region.width for button in buttons]
            assert max(widths) - min(widths) <= 1

    asyncio.run(verify())
