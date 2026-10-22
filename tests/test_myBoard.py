"""Board placement, confirmed moves, and the myBoard command."""

import asyncio
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

from organiseMyProjects.myBoard import main
from organiseMyProjects.requirementBoard import (
    CommandSnapshot,
    RequirementCard,
    RequirementDraft,
    RequirementGit,
    detailParts,
    _documentJoin,
    _documentSplit,
    boardLoad,
    cardFormat,
    cardMove,
    checkFindingsLoad,
    findingsSelect,
    gitContextLoad,
    projectRootFind,
    pytestSelect,
    requirementCreate,
    requirementGitLoad,
)

REQUIRES_TEXTUAL = pytest.mark.skipif(
    importlib.util.find_spec("textual") is None,
    reason="textual is not installed; run in the ompr Conda environment",
)

_INDEX = """# Requirements

Next available number: 005

## Requirement index

| Req ID | Requirement | Description | Status | Agent Prompt | Architecture Decisions |
| --- | --- | --- | --- | --- | --- |
| 001 | [First](features/001-first.md) | First requirement. | Completed | [Prompt](prompt/001-first.md) | Not required |
| 002 | [Second](features/002-second.md) | Second requirement. | ToDo | [Prompt](prompt/002-second.md) | Not required |
| 003 | [Third](features/003-third.md) | Third requirement. | ToDo | [Prompt](prompt/003-third.md) | Not required |
| 004 | [Fourth](features/004-fourth.md) | Fourth requirement. | InProgress | [Prompt](prompt/004-fourth.md) | Not required |
"""

_INCREMENT = """# Current Development Increment

## Increment

0.9 — Fixture increment

## Status

In progress

## Objective

Keep this sentence: fixture objective stays.

## Requirements

- [002: Second](requirements/features/002-second.md) — ToDo
- [004: Fourth](requirements/features/004-fourth.md) — InProgress; active fixture.

## Backlog

- [003: Third](requirements/features/003-third.md) — ToDo

## Planned order

1. Requirement 004.
"""


def featureText(number: str, title: str, status: str) -> str:
    return f"""# {number}: {title}

## Status

{status}

## Outcome

As a tester, I need {title} so that the board can place it.

## Context

Fixture.

## Scope

- Fixture behaviour.

## Out of scope

- Everything else.

## Acceptance criteria

1. Given the fixture, when the board loads, then {number} is visible.

## Dependencies and decisions

- None.

## Verification

- pytest

## Change history

- 2026-10-22: created — fixture.
"""


def boardFixture(tmp_path: Path) -> Path:
    """Create a four-card project with one requirement in each column."""
    root = tmp_path / "proj"
    features = root / "project" / "requirements" / "features"
    prompts = root / "project" / "requirements" / "prompt"
    features.mkdir(parents=True)
    prompts.mkdir()
    (root / "project" / "requirements" / "requirementsIndex.md").write_text(_INDEX)
    (root / "project" / "currentIncrement.md").write_text(_INCREMENT)
    cards = (
        ("001", "First", "Completed"),
        ("002", "Second", "ToDo"),
        ("003", "Third", "ToDo"),
        ("004", "Fourth", "InProgress"),
    )
    for number, title, status in cards:
        name = f"{number}-{title.lower()}.md"
        (features / name).write_text(featureText(number, title, status))
        (prompts / name).write_text(f"# {number}: Implement {title}\n")
    return root


def fileBytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def testProjectRootWalksUp(tmp_path: Path):
    root = boardFixture(tmp_path)
    nested = root / "project" / "requirements" / "features"
    assert projectRootFind(nested) == root.resolve()


def testColumnsPlaceEachRequirementOnce(tmp_path: Path):
    board = boardLoad(boardFixture(tmp_path))
    placed = {card.number: card.column for card in board.cards}
    assert placed == {
        "001": "Completed",
        "002": "ToDo",
        "003": "Backlog",
        "004": "InProgress",
    }
    assert board.release == "0.9"
    assert board.nextNumber == "005"


def testMoveBacklogToTodoKeepsStatus(tmp_path: Path):
    root = boardFixture(tmp_path)
    result = cardMove(root, "3", "ToDo", dryRun=False, today="2026-10-22")
    assert result.source == "Backlog"
    assert result.target == "ToDo"
    board = boardLoad(root)
    card = board.cardGet("003")
    assert card.column == "ToDo"
    assert card.status == "ToDo"
    increment = (root / "project" / "currentIncrement.md").read_text()
    assert "fixture objective stays." in increment
    assert "1. Requirement 004." in increment
    requirements = increment.split("## Backlog", 1)[0]
    backlog = increment.split("## Backlog", 1)[1]
    assert "features/003-third.md" in requirements
    assert "features/003-third.md" not in backlog
    history = (
        root / "project" / "requirements" / "features" / "003-third.md"
    ).read_text()
    assert "status " not in history.split("## Change history", 1)[1]


def testMoveToInProgressUpdatesEveryDocument(tmp_path: Path):
    root = boardFixture(tmp_path)
    cardMove(root, "003", "InProgress", dryRun=False, today="2026-10-22")
    record = (
        root / "project" / "requirements" / "features" / "003-third.md"
    ).read_text()
    index = (root / "project" / "requirements" / "requirementsIndex.md").read_text()
    increment = (root / "project" / "currentIncrement.md").read_text()
    assert "## Status\n\nInProgress\n" in record
    assert "status ToDo -> InProgress — myBoard" in record
    assert "As a tester, I need Third" in record
    assert (
        "| 003 | [Third](features/003-third.md) | Third requirement. | InProgress |"
        in index
    )
    requirements = increment.split("## Backlog", 1)[0]
    backlog = increment.split("## Backlog", 1)[1]
    assert "features/003-third.md" in requirements
    assert "— InProgress" in requirements
    assert "features/003-third.md" not in backlog
    assert boardLoad(root).cardGet("003").column == "InProgress"


def testDryRunLeavesFilesUntouched(tmp_path: Path):
    root = boardFixture(tmp_path)
    before = fileBytes(root)
    result = cardMove(root, "003", "InProgress", dryRun=True, today="2026-10-22")
    assert result.changed
    assert fileBytes(root) == before
    assert main(["--project", str(root), "move", "003", "Completed"]) == 0
    assert fileBytes(root) == before


def testSameColumnIsUnchanged(tmp_path: Path):
    root = boardFixture(tmp_path)
    before = fileBytes(root)
    result = cardMove(root, "004", "InProgress", dryRun=False, today="2026-10-22")
    assert not result.changed
    assert fileBytes(root) == before


def testCompletedDropsBacklogMention(tmp_path: Path):
    root = boardFixture(tmp_path)
    cardMove(root, "003", "Completed", dryRun=False, today="2026-10-22")
    card = boardLoad(root).cardGet("003")
    assert card.column == "Completed"
    assert card.status == "Completed"
    increment = (root / "project" / "currentIncrement.md").read_text()
    backlog = increment.split("## Backlog", 1)[1].split("## Planned order", 1)[0]
    assert "features/003-third.md" not in backlog


def testCreateAddsBacklogRequirement(tmp_path: Path):
    root = boardFixture(tmp_path)
    draft = RequirementDraft(
        name="fifthItem",
        title="Fifth item",
        description="A captured requirement.",
        outcome="As a tester, I need a fifth card so that create is visible.",
    )
    before = fileBytes(root)
    preview = requirementCreate(root, draft, dryRun=True, today="2026-10-22")
    assert preview.number == "005"
    assert preview.changed
    assert fileBytes(root) == before
    created = requirementCreate(root, draft, dryRun=False, today="2026-10-22")
    assert created.filename == "005-fifthItem.md"
    board = boardLoad(root)
    assert board.nextNumber == "006"
    index = (root / "project" / "requirements" / "requirementsIndex.md").read_text()
    assert "Next available number: 006\n\n## Requirement index" in index
    assert board.cardGet("005").column == "Backlog"
    record = (
        root / "project" / "requirements" / "features" / "005-fifthItem.md"
    ).read_text()
    assert "# 005: Fifth item" in record
    assert "## Status\n\nToDo\n" in record
    assert "2026-10-22: created — myBoard." in record


def testCreateRejectsABadName(tmp_path: Path):
    root = boardFixture(tmp_path)
    draft = RequirementDraft(
        name="Not-camel",
        title="Bad",
        description="Bad.",
        outcome="As a tester, I need a valid name so that the file conforms.",
    )
    with pytest.raises(ValueError, match="camelCase"):
        requirementCreate(root, draft, dryRun=False)


def testDocumentsRoundTrip():
    root = Path(__file__).resolve().parents[1]
    samples = [
        root / "project" / "currentIncrement.md",
        root / "project" / "requirements" / "requirementsIndex.md",
        root
        / "project"
        / "requirements"
        / "features"
        / "012-sharedTuiButtonPresentation.md",
    ]
    for path in samples:
        text = path.read_text(encoding="utf-8")
        assert _documentJoin(*_documentSplit(text)) == text


def testRepositoryBoardLoads():
    root = Path(__file__).resolve().parents[1]
    board = boardLoad(root)
    numbers = [card.number for card in board.cards]
    featureNumbers = {
        path.name[:3]
        for path in (root / "project" / "requirements" / "features").glob("*.md")
    }
    assert set(numbers) == featureNumbers
    assert len(numbers) == len(set(numbers))
    assert {card.column for card in board.cards} <= {
        "Backlog",
        "ToDo",
        "InProgress",
        "Completed",
    }


def testListIsNotMarkedAsDryRun(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    root = boardFixture(tmp_path)
    assert main(["--project", str(root), "list"]) == 0
    captured = capsys.readouterr().out
    assert "Backlog" in captured
    assert "[]" not in captured


def testListJson(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    root = boardFixture(tmp_path)
    assert main(["--project", str(root), "list", "--json"]) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    placed = {item["number"]: item["column"] for item in payload}
    assert placed["003"] == "Backlog"
    assert ">\n" not in captured.out


def testCheckSelectsDriftForOneCard(tmp_path: Path):
    root = boardFixture(tmp_path)
    index = root / "project" / "requirements" / "requirementsIndex.md"
    index.write_text(
        index.read_text().replace(
            "| ToDo | [Prompt](prompt/003-third.md)",
            "| Completed | [Prompt](prompt/003-third.md)",
        )
    )
    card = boardLoad(root).cardGet("003")
    assert card.drift
    chosen = findingsSelect(checkFindingsLoad(root), card) or ()
    assert any(item.ruleId == "REQ-002" for item in chosen)
    assert all(
        "003-third.md" in f"{item.path}\n{item.message}" or "003" in item.message
        for item in chosen
    )


def _sampleCard() -> RequirementCard:
    return RequirementCard(
        number="002",
        title="Second",
        description="",
        status="ToDo",
        indexStatus="ToDo",
        filename="002-second.md",
        outcome="",
        onIncrement=True,
        inBacklog=False,
        verification="",
    )


def testPytestStaysWithTheRequirementItNames():
    snapshot = CommandSnapshot(
        1,
        "1 failed, 3 passed in 0.2s",
        "\n".join(
            [
                "tests/test_myBoard.py:12: assert False",
                "FAILED tests/test_other.py::test_unrelated - assert 0",
            ]
        ),
    )
    mine = pytestSelect(snapshot, (), "pytest tests/test_myBoard.py")
    by_path = pytestSelect(snapshot, ("tests/test_myBoard.py",), "")
    other = pytestSelect(snapshot, (), "- pytest tests/test_other.py")
    module_only = pytestSelect(snapshot, (), "runLinter on myBoard.py")
    untouched = pytestSelect(snapshot, ("src/notes.txt",), "- pytest")
    assert mine == ("tests/test_myBoard.py:12: assert False",)
    assert by_path == mine
    assert module_only == ()
    assert other == ("FAILED tests/test_other.py::test_unrelated - assert 0",)
    assert untouched == ()
    assert pytestSelect(None, (), "pytest tests/test_myBoard.py") is None
    shown = cardFormat(_sampleCard(), pytestLines=mine)
    assert "tests/test_myBoard.py:12" in shown
    assert "test_other.py" not in shown
    assert "no failures for this requirement" in cardFormat(
        _sampleCard(), pytestLines=untouched
    )
    assert "pytest: not run" in cardFormat(_sampleCard())


def testGitLinksTheRequirementId(tmp_path: Path):
    root = boardFixture(tmp_path)
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "board@example.com"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "Board Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "checkout", "-b", "003-work"], cwd=root, check=True, capture_output=True
    )
    (root / "notes.txt").write_text("003\n")
    subprocess.run(["git", "add", "notes.txt"], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "003: start the third requirement"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    context = gitContextLoad(root, "0.9")
    assert context.available
    assert context.branch == "003-work"
    assert context.aheadMain == 1
    assert context.releaseBranch == "release/0.9"
    assert context.aheadRelease is None
    linked = requirementGitLoad(root, "003")
    assert "003-work" in linked.branches
    assert any(subject.startswith("003:") for _revision, subject in linked.commits)
    assert "notes.txt" in linked.paths
    other = requirementGitLoad(root, "002")
    assert other.branches == ()
    assert other.commits == ()
    detail = cardFormat(boardLoad(root).cardGet("003"), linked)
    assert "Branch: 003-work" in detail
    assert "Commits:" in detail
    assert "\n  notes.txt\n" in detail


def testChangedFilesAreOnePerLine():
    git = RequirementGit(
        ("feature/board",),
        (("abc1234", "004: start the board"),),
        ("board.txt", "notes.txt"),
    )
    parts = detailParts(_sampleCard(), git)
    assert [text for role, text in parts if role == "file"] == [
        "board.txt",
        "notes.txt",
    ]
    plain = cardFormat(_sampleCard(), git)
    assert "Changed files:\n  board.txt\n  notes.txt\n" in plain


def testBranchFollowsAnUnmergedRequirementCommit(tmp_path: Path):
    root = tmp_path / "proj"
    root.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "board@example.com"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "Board Test"], cwd=root, check=True)
    (root / "readme.txt").write_text("start\n")
    subprocess.run(["git", "add", "readme.txt"], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "checkout", "-b", "feature/board"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "board.txt").write_text("004\n")
    subprocess.run(["git", "add", "board.txt"], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "004: start the board"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "board.txt").write_text("004\nmore\n")
    subprocess.run(["git", "add", "board.txt"], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "adjust the board"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    linked = requirementGitLoad(root, "004")
    assert linked.branches == ("feature/board",)
    assert [subject for _revision, subject in linked.commits] == [
        "adjust the board",
        "004: start the board",
    ]
    assert "board.txt" in linked.paths
    assert "readme.txt" not in linked.paths


def _colourAverage(colour) -> float:
    return (colour.r + colour.g + colour.b) / 3


def _assertDarkContrast(ink, surface) -> None:
    """Fail when text is not clearly lighter than a dark working surface."""
    assert surface.a == 1
    row = _colourAverage(surface)
    assert row < 80
    assert abs(_colourAverage(ink) - row) > 80


@REQUIRES_TEXTUAL
def testSelectedCardStaysReadable(tmp_path: Path):
    from textual.widgets import Label, ListView, Static

    from organiseMyProjects.myBoardTui import BoardApp

    root = boardFixture(tmp_path)

    async def verify():
        app = BoardApp(root)
        async with app.run_test(size=(140, 36)) as pilot:
            view = None
            for _attempt in range(20):
                await pilot.pause()
                view = app.query_one("#list-ToDo", ListView)
                if view.children:
                    break
            assert view is not None and view.children
            # Focus alone leaves the cursor unset. The row highlight is the index.
            view.focus()
            view.index = 0
            await pilot.pause()
            highlighted = view.highlighted_child
            assert highlighted is not None
            column = view.parent
            _assertDarkContrast(column.styles.color, column.styles.background)
            _assertDarkContrast(view.styles.color, view.styles.background)
            title = app.query_one("#title-ToDo", Static)
            _assertDarkContrast(title.styles.color, column.styles.background)
            _assertDarkContrast(
                highlighted.query_one(Label).styles.color,
                highlighted.styles.background,
            )
            plain = app.query_one("#list-Backlog", ListView).children[0]
            _assertDarkContrast(
                plain.query_one(Label).styles.color,
                plain.styles.background,
            )

    asyncio.run(verify())


@REQUIRES_TEXTUAL
def testBoardMoveFromTheColumns(tmp_path: Path):
    from textual.widgets import Label, ListView

    from organiseMyProjects.myBoardTui import BoardApp

    root = boardFixture(tmp_path)

    async def verify():
        app = BoardApp(root)
        async with app.run_test(size=(140, 36)) as pilot:
            labels = []
            for _attempt in range(20):
                await pilot.pause()
                labels = [widget.render().plain for widget in app.query(Label)]
                if any(text.startswith("003") for text in labels):
                    break
            assert any(text.startswith("003") for text in labels)
            titles = [widget.render().plain for widget in app.query(".column-title")]
            assert any(text.startswith("Backlog") for text in titles)
            backlog = app.query_one("#list-Backlog", ListView)
            backlog.focus()
            backlog.index = 0
            await pilot.press("right_square_bracket")
            await pilot.pause()
            await pilot.click("#move-apply")
            for _attempt in range(20):
                await pilot.pause()
                if boardLoad(root).cardGet("003").column == "ToDo":
                    break
            assert boardLoad(root).cardGet("003").column == "ToDo"
            assert boardLoad(root).cardGet("003").status == "ToDo"

    asyncio.run(verify())


@REQUIRES_TEXTUAL
def testDetailIgnoresColumnMoves(tmp_path: Path):
    from textual.widgets import ListView

    from organiseMyProjects.myBoardTui import BoardApp, DetailScreen

    root = boardFixture(tmp_path)

    async def verify():
        app = BoardApp(root)
        async with app.run_test(size=(140, 36)) as pilot:
            backlog = None
            for _attempt in range(20):
                await pilot.pause()
                backlog = app.query_one("#list-Backlog", ListView)
                if backlog.children:
                    break
            assert backlog is not None and backlog.children
            backlog.focus()
            backlog.index = 0
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, DetailScreen)
            shown = {
                key.description.casefold() for key in app.screen.query("FooterKey")
            }
            assert "move left" not in shown
            assert "move right" not in shown
            await pilot.press("right_square_bracket", "left_square_bracket")
            await pilot.pause()
            assert not app.query("ConfirmMove")
            assert boardLoad(root).cardGet("003").column == "Backlog"

    asyncio.run(verify())


@REQUIRES_TEXTUAL
def testRightClickSelectsAndLeftClickOpensTheCard(tmp_path: Path):
    from textual.widgets import ListView

    from organiseMyProjects.myBoardTui import BoardApp, ConfirmMove, DetailScreen

    root = boardFixture(tmp_path)

    async def verify():
        app = BoardApp(root)
        async with app.run_test(size=(140, 36)) as pilot:
            backlog = None
            for _attempt in range(20):
                await pilot.pause()
                backlog = app.query_one("#list-Backlog", ListView)
                if backlog.children:
                    break
            assert backlog is not None and backlog.children
            card = backlog.children[0]
            await pilot.click(card, button=3)
            await pilot.pause()
            assert not isinstance(app.screen, DetailScreen)
            assert backlog.highlighted_child is card
            await pilot.press("right_square_bracket")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmMove)
            assert boardLoad(root).cardGet("003").column == "Backlog"
            await pilot.click("#move-cancel")
            await pilot.pause()
            await pilot.click(card)
            await pilot.pause()
            assert isinstance(app.screen, DetailScreen)
            assert backlog.highlighted_child is card

    asyncio.run(verify())


@REQUIRES_TEXTUAL
def testSelectingInAnotherColumnClearsTheFirst(tmp_path: Path):
    from textual.widgets import ListView

    from organiseMyProjects.myBoardTui import BoardApp

    root = boardFixture(tmp_path)

    async def verify():
        app = BoardApp(root)
        async with app.run_test(size=(140, 36)) as pilot:
            backlog = completed = None
            for _attempt in range(20):
                await pilot.pause()
                backlog = app.query_one("#list-Backlog", ListView)
                completed = app.query_one("#list-Completed", ListView)
                if backlog.children and completed.children:
                    break
            assert backlog is not None and backlog.children
            assert completed is not None and completed.children
            await pilot.click(backlog.children[0], button=3)
            await pilot.pause()
            assert backlog.highlighted_child is backlog.children[0]
            await pilot.click(completed.children[0], button=3)
            await pilot.pause()
            assert completed.highlighted_child is completed.children[0]
            assert backlog.highlighted_child is None
            assert app.activeCard().number == "001"

    asyncio.run(verify())


@REQUIRES_TEXTUAL
def testDetailShowsFilesOnSeparateLines(tmp_path: Path):
    from textual.widgets import Static

    from organiseMyProjects.myBoardTui import BoardApp, DetailScreen

    root = boardFixture(tmp_path)

    async def verify():
        app = BoardApp(root)
        async with app.run_test(size=(100, 32)) as pilot:
            backlog = None
            for _attempt in range(20):
                await pilot.pause()
                backlog = app.query_one("#list-Backlog")
                if backlog.children:
                    break
            assert backlog is not None and backlog.children
            backlog.focus()
            backlog.index = 0
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, DetailScreen)
            app.gitCards["003"] = RequirementGit(
                branches=("003-work",),
                commits=(("abc1234", "003: start"),),
                paths=("notes.txt", "other.txt"),
            )
            app.screen.textRefresh()
            files = []
            for _attempt in range(20):
                await pilot.pause()
                files = list(app.screen.query(".detail-file"))
                if len(files) == 2:
                    break
            assert [widget.render().plain for widget in files] == [
                "notes.txt",
                "other.txt",
            ]
            assert files[1].region.y > files[0].region.y
            title = app.screen.query_one(".detail-title", Static)
            assert title.styles.text_style.bold
            assert (
                title.styles.color.r,
                title.styles.color.g,
                title.styles.color.b,
            ) == (
                35,
                155,
                120,
            )

    asyncio.run(verify())
