"""Textual requirement board.

The widgets call ``requirementBoard``. They do not decide status rules or
write documents except by asking that module to apply a confirmed move.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static

from organiseMyProjects.requirementBoard import (
    COLUMNS,
    Board,
    CheckFinding,
    CommandSnapshot,
    GitContext,
    LintSnapshot,
    RequirementCard,
    RequirementGit,
    boardLoad,
    cardFormat,
    cardMove,
    changeApply,
    checkFindingsLoad,
    findingsSelect,
    gitContextLoad,
    lintSelect,
    lintSnapshotLoad,
    pytestSnapshotLoad,
    requirementGitLoad,
)

_THEME = Path(__file__).with_name("myStyles.css")


class CardItem(ListItem):
    """One requirement in a column."""

    def __init__(self, card: RequirementCard) -> None:
        mark = " !" if card.drift else ""
        super().__init__(Label(f"{card.number}  {card.title}{mark}"))
        self.card = card


class ConfirmMove(ModalScreen[bool]):
    """Ask before a move writes the requirement documents."""

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Static(self.message, id="confirm-text")
            with Horizontal(classes="button-group"):
                yield Button("Apply", id="move-apply", variant="success")
                yield Button("Cancel", id="move-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "move-apply")


class DetailScreen(Screen):
    """Outcome, linked Git history, and check results for one card."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("c", "checks", "Checks"),
        Binding("n", "lint", "Lint"),
        Binding("t", "pytest", "pytest"),
    ]

    def __init__(self, card: RequirementCard) -> None:
        super().__init__()
        self.card = card

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static("", id="detail-text")
        yield Footer()

    def on_mount(self) -> None:
        self.textRefresh()
        board = self.boardApp
        board.gitCardLoad(self.card.number)

    def textRefresh(self) -> None:
        """Redraw the detail from the signals the board has loaded."""
        board = self.boardApp
        git = board.gitCards.get(self.card.number)
        findings = findingsSelect(board.checkFindings, self.card)
        lint = None
        if board.lintFindings is not None:
            paths = () if git is None else git.paths
            lint = lintSelect(board.lintFindings, paths)
        self.query_one("#detail-text", Static).update(
            cardFormat(self.card, git, findings, lint, board.pytestSummary)
        )

    @property
    def boardApp(self) -> BoardApp:
        """Return the owning board."""
        app = self.app
        assert isinstance(app, BoardApp)
        return app

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_checks(self) -> None:
        self.boardApp.checksLoad()

    def action_lint(self) -> None:
        self.boardApp.lintLoad()

    def action_pytest(self) -> None:
        self.boardApp.pytestLoad()


class BoardApp(App):
    """Four-column board for the project root it was given."""

    CSS_PATH = _THEME
    CSS = """
    #board-strip {
        height: 3;
        padding: 0 1;
        color: #60788e;
    }
    #columns {
        height: 1fr;
    }
    .column {
        width: 1fr;
        height: 1fr;
        border-right: solid #d9e5ef;
    }
    .column-title {
        height: 1;
        padding: 0 1;
        text-style: bold;
        color: #239b78;
    }
    ListView {
        height: 1fr;
        background: #f7f7f5;
    }
    ListItem {
        padding: 0 1;
    }
    ListItem.-highlight {
        background: #243545;
        color: #f5f8fb;
    }
    ConfirmMove {
        align: center middle;
    }
    #confirm-box {
        width: 72;
        height: auto;
        padding: 1 2;
        background: #101f2e;
        color: #f5f8fb;
        border: solid #239b78;
    }
    #detail-text {
        padding: 1 2;
    }
    """
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("left", "focus_left", "Left", show=False),
        Binding("right", "focus_right", "Right", show=False),
        Binding("left_square_bracket", "move_left", "Move left"),
        Binding("right_square_bracket", "move_right", "Move right"),
        Binding("c", "checks", "Checks"),
        Binding("n", "lint", "Lint"),
        Binding("t", "pytest", "pytest"),
        Binding("g", "refresh", "Refresh"),
    ]

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root
        self.board = Board(root, "", "", ())
        self.gitContext = GitContext(False, "", False, None, None, "", None, None)
        self.gitCards: dict[str, RequirementGit] = {}
        self.checkFindings: tuple[CheckFinding, ...] | None = None
        self.lintFindings: tuple[CheckFinding, ...] | None = None
        self.lintSummary = ""
        self.pytestSummary = ""
        self.pendingMove: tuple[str, str] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("loading", id="board-strip")
        with Horizontal(id="columns"):
            for column in COLUMNS:
                with Vertical(classes="column"):
                    yield Static(column, classes="column-title", id=f"title-{column}")
                    yield ListView(id=f"list-{column}")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "myBoard"
        self.sub_title = self.root.name
        self.run_worker(self.boardFirst, exclusive=True, group="board")

    async def boardFirst(self) -> None:
        """Load the columns, then the cheap Git strip."""
        await self.boardRefresh()
        self.gitLoad()

    async def boardRefresh(self, select: str | None = None) -> None:
        """Reload the four columns from disk."""
        self.board = boardLoad(self.root)
        selectedView: ListView | None = None
        for column in COLUMNS:
            cards = [card for card in self.board.cards if card.column == column]
            self.query_one(f"#title-{column}", Static).update(f"{column}  {len(cards)}")
            view = self.query_one(f"#list-{column}", ListView)
            await view.clear()
            for card in cards:
                await view.append(CardItem(card))
            if select and any(card.number == select for card in cards):
                for index, card in enumerate(cards):
                    if card.number == select:
                        view.index = index
                        selectedView = view
        self.stripRefresh()
        if selectedView is not None:
            selectedView.focus()
        elif not isinstance(self.focused, ListView):
            self.columnFocus(0)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, CardItem):
            self.push_screen(DetailScreen(event.item.card))

    def action_focus_left(self) -> None:
        self.columnFocus(-1)

    def action_focus_right(self) -> None:
        self.columnFocus(1)

    def action_move_left(self) -> None:
        self.moveAsk(-1)

    def action_move_right(self) -> None:
        self.moveAsk(1)

    def action_checks(self) -> None:
        self.checksLoad()

    def action_lint(self) -> None:
        self.lintLoad()

    def action_pytest(self) -> None:
        self.pytestLoad()

    def action_refresh(self) -> None:
        self.boardReload()
        self.gitLoad()

    def boardReload(self, number: str | None = None) -> None:
        """Reload the columns on the application thread."""

        async def refresh() -> None:
            await self.boardRefresh(number)

        self.run_worker(refresh, exclusive=True, group="board")

    def columnFocus(self, step: int) -> None:
        """Move focus by one column, wrapping at the ends."""
        current = self.focusedColumn()
        index = COLUMNS.index(current) if current in COLUMNS else 0
        target = COLUMNS[(index + step) % len(COLUMNS)]
        self.query_one(f"#list-{target}", ListView).focus()

    def moveAsk(self, step: int) -> None:
        """Preview a one-column move and ask before writing."""
        card = self.activeCard()
        if card is None:
            self.notify("Select a requirement first")
            return
        index = COLUMNS.index(card.column)
        nextIndex = index + step
        if nextIndex < 0 or nextIndex >= len(COLUMNS):
            return
        target = COLUMNS[nextIndex]
        try:
            plan = cardMove(self.root, card.number, target, dryRun=True)
        except (OSError, ValueError) as exc:
            self.notify(str(exc), severity="error")
            return
        if not plan.changed:
            self.notify(plan.note)
            return
        files = "\n".join(
            change.path.relative_to(self.root).as_posix() for change in plan.changes
        )
        self.pendingMove = (card.number, target)
        self.push_screen(ConfirmMove(f"{plan.note}\n\n{files}"), self.moveFinish)

    def moveFinish(self, apply: bool | None) -> None:
        """Write the previewed move after Apply."""
        pending = self.pendingMove
        self.pendingMove = None
        if not apply or pending is None:
            return
        number, target = pending
        try:
            plan = cardMove(self.root, number, target, dryRun=True)
            changeApply(plan.changes)
        except (OSError, ValueError) as exc:
            self.notify(str(exc), severity="error")
            return
        self.boardReload(number)

    def activeCard(self) -> RequirementCard | None:
        """Return the highlighted card in the focused column."""
        column = self.focusedColumn()
        if not column:
            return None
        item = self.query_one(f"#list-{column}", ListView).highlighted_child
        if isinstance(item, CardItem):
            return item.card
        return None

    def focusedColumn(self) -> str:
        """Return the column name of the focused list, or an empty string."""
        focused = self.focused
        if (
            isinstance(focused, ListView)
            and focused.id
            and focused.id.startswith("list-")
        ):
            return focused.id.removeprefix("list-")
        return ""

    def gitLoad(self) -> None:
        """Refresh the branch strip without blocking the board."""
        self.run_worker(
            self.gitWork, thread=True, exclusive=True, group="git", exit_on_error=False
        )

    def gitWork(self) -> None:
        context = gitContextLoad(self.root, self.board.release)
        self.call_from_thread(self.gitShow, context)

    def gitShow(self, context: GitContext) -> None:
        self.gitContext = context
        self.stripRefresh()

    def gitCardLoad(self, number: str) -> None:
        """Load linked branches for the open card."""
        self.run_worker(
            lambda: self.gitCardWork(number),
            thread=True,
            exclusive=True,
            group="git-card",
            exit_on_error=False,
        )

    def gitCardWork(self, number: str) -> None:
        try:
            linked = requirementGitLoad(self.root, number)
        except (OSError, ValueError) as exc:
            self.call_from_thread(self.notify, str(exc))
            return
        self.call_from_thread(self.gitCardShow, number, linked)

    def gitCardShow(self, number: str, linked: RequirementGit) -> None:
        self.gitCards[number] = linked
        self.detailRefresh()

    def checksLoad(self) -> None:
        """Run manageProject checks in the background."""
        self.notify("Running checks")
        self.run_worker(
            self.checksWork,
            thread=True,
            exclusive=True,
            group="checks",
            exit_on_error=False,
        )

    def checksWork(self) -> None:
        try:
            findings = checkFindingsLoad(self.root)
        except (OSError, ValueError) as exc:
            self.call_from_thread(self.notify, str(exc))
            return
        self.call_from_thread(self.checksShow, findings)

    def checksShow(self, findings: tuple[CheckFinding, ...]) -> None:
        self.checkFindings = findings
        self.stripRefresh()
        self.detailRefresh()

    def lintLoad(self) -> None:
        """Run runLinter in the background."""
        self.lintSummary = "lint running"
        self.stripRefresh()
        self.run_worker(
            self.lintWork,
            thread=True,
            exclusive=True,
            group="lint",
            exit_on_error=False,
        )

    def lintWork(self) -> None:
        try:
            snapshot = lintSnapshotLoad(self.root)
        except (OSError, ValueError) as exc:
            self.call_from_thread(self.notify, str(exc))
            return
        self.call_from_thread(self.lintShow, snapshot)

    def lintShow(self, snapshot: LintSnapshot) -> None:
        self.lintFindings = snapshot.findings
        self.lintSummary = snapshot.summary
        self.stripRefresh()
        self.detailRefresh()

    def pytestLoad(self) -> None:
        """Run pytest in the background."""
        self.pytestSummary = "pytest running"
        self.stripRefresh()
        self.detailRefresh()
        self.run_worker(
            self.pytestWork,
            thread=True,
            exclusive=True,
            group="pytest",
            exit_on_error=False,
        )

    def pytestWork(self) -> None:
        snapshot = pytestSnapshotLoad(self.root)
        self.call_from_thread(self.pytestShow, snapshot)

    def pytestShow(self, snapshot: CommandSnapshot) -> None:
        self.pytestSummary = snapshot.summary
        self.stripRefresh()
        self.detailRefresh()

    def stripRefresh(self) -> None:
        """Redraw the project strip from the latest signals."""
        if not self.is_mounted:
            return
        failures = warnings = None
        if self.checkFindings is not None:
            failures = sum(item.severity == "FAILURE" for item in self.checkFindings)
            warnings = sum(item.severity == "WARNING" for item in self.checkFindings)
        checks = (
            "check not run"
            if failures is None
            else f"check {failures} failures, {warnings} warnings"
        )
        parts = [
            self.gitContext.summary(),
            checks,
            self.lintSummary or "lint not run",
            self.pytestSummary or "pytest not run",
        ]
        self.query_one("#board-strip", Static).update(" | ".join(parts))

    def detailRefresh(self) -> None:
        """Redraw the detail screen when it is the screen in front."""
        if isinstance(self.screen, DetailScreen):
            self.screen.textRefresh()
