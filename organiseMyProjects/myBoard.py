"""Command line for the requirement board.

``myBoard`` with no subcommand opens the Textual board. ``list``, ``show``,
``move``, ``create``, ``edit``, ``check``, ``lint`` and ``pytest`` run without
a terminal UI. Changes stay as a dry-run until ``--confirm``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from organiseMyProjects.logUtils import getLogger, line, runStart, setApplication
from organiseMyProjects.requirementBoard import (
    COLUMNS,
    RequirementDraft,
    RequirementUpdate,
    boardDump,
    boardFormat,
    boardLoad,
    cardFormat,
    cardMove,
    changeApply,
    checkFindingsLoad,
    columnNormalise,
    findingsSelect,
    gitContextLoad,
    lintSnapshotLoad,
    numberNormalise,
    projectRootFind,
    pytestSnapshotLoad,
    requirementCreate,
    requirementGitLoad,
    requirementUpdate,
)
from organiseMyProjects.version import VERSION


def buildParser() -> argparse.ArgumentParser:
    """Return the myBoard argument parser."""
    common = _commonParser()
    parser = argparse.ArgumentParser(
        prog="myBoard",
        description="Show and update requirements for the project you are in.",
        parents=[common],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "columns: " + ", ".join(COLUMNS) + "\n\n"
            "myBoard\n"
            "myBoard list\n"
            "myBoard show 012\n"
            "myBoard move 012 InProgress --confirm"
        ),
    )
    parser.add_argument("--version", action="version", version=VERSION)
    _commandsAdd(parser, common)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run a myBoard command."""
    raw = list(sys.argv[1:] if argv is None else argv)
    project, cleaned = _projectExtract(raw)
    args = buildParser().parse_args(cleaned)
    if project is not None:
        args.project = project
    return commandRun(args)


def commandRun(args: argparse.Namespace) -> int:
    """Run the board, or a scriptable command with the standard log boundary."""
    setApplication("myBoard")
    if args.command is None:
        return boardLaunch(args)
    # JSON must stay free of the stdout log markers.
    if getattr(args, "json", False):
        return commandExecute(args, None, False)

    # Only document-changing commands must announce their dry-run mode.
    dryRun = args.command in {"move", "create", "edit"} and not getattr(
        args, "confirm", False
    )
    logger = getLogger(includeConsole=True, dryRun=dryRun)
    runStart()
    logger.doing("starting")
    line()
    code = commandExecute(args, logger, dryRun)
    line()
    logger.done("finished")
    return code


## commands


def commandExecute(args: argparse.Namespace, logger, dryRun: bool) -> int:
    """Dispatch one scriptable command. The board is handled before this."""
    try:
        root = projectRootFind(args.project or Path.cwd())
    except FileNotFoundError as exc:
        reportWrite(logger, str(exc))
        return 2
    handlers = {
        "list": commandList,
        "show": commandShow,
        "move": commandMove,
        "create": commandCreate,
        "edit": commandEdit,
        "check": commandCheck,
        "lint": commandLint,
        "pytest": commandPytest,
    }
    try:
        return handlers[args.command](args, root, logger, dryRun)
    except (OSError, ValueError) as exc:
        reportWrite(logger, str(exc))
        return 1


def commandCheck(args: argparse.Namespace, root: Path, logger, dryRun: bool) -> int:
    """Print manageProject check findings, optionally for one requirement."""
    del dryRun
    findings = checkFindingsLoad(root)
    if args.number:
        card = boardLoad(root).cardGet(numberNormalise(args.number))
        chosen = findingsSelect(findings, card) or ()
        if not chosen:
            print(f"{card.number} has no check findings")
        for item in chosen:
            print(f"{item.ruleId} {item.severity}: {item.message}")
        failures = sum(item.severity == "FAILURE" for item in chosen)
    else:
        failures = sum(item.severity == "FAILURE" for item in findings)
        warnings = sum(item.severity == "WARNING" for item in findings)
        print(f"{failures} failures, {warnings} warnings")
        for item in findings:
            if item.severity == "FAILURE":
                print(f"{item.ruleId}: {item.message}")
    if logger is not None:
        logger.value("failures", failures)
    return 1 if failures else 0


def commandCreate(args: argparse.Namespace, root: Path, logger, dryRun: bool) -> int:
    """Create the next backlog requirement."""
    draft = RequirementDraft(
        name=args.name,
        title=args.title,
        description=args.description,
        outcome=args.outcome,
        context=args.context,
        scope=args.scope,
        excluded=args.excluded,
        acceptance=args.acceptance,
        verification=args.verification,
    )
    plan = requirementCreate(root, draft, dryRun=True)
    changeReport(root, plan.changes, logger)
    if dryRun:
        reportWrite(logger, "dry-run left the files unchanged")
        return 0
    changeApply(plan.changes)
    if logger is not None:
        logger.value("created", plan.number)
    else:
        print(plan.number)
    return 0


def commandEdit(args: argparse.Namespace, root: Path, logger, dryRun: bool) -> int:
    """Edit selected metadata and prose fields on one requirement."""
    update = RequirementUpdate(
        title=args.title,
        description=args.description,
        outcome=args.outcome,
        context=args.context,
        scope=args.scope,
        excluded=args.excluded,
        acceptance=args.acceptance,
        dependencies=args.dependencies,
        verification=args.verification,
    )
    plan = requirementUpdate(root, args.number, update, dryRun=True)
    if not plan.changed:
        reportWrite(logger, f"{plan.number} already has those values")
        return 0
    changeReport(root, plan.changes, logger)
    if dryRun:
        reportWrite(logger, "dry-run left the files unchanged")
        return 0
    changeApply(plan.changes)
    if logger is not None:
        logger.value("edited", plan.number)
    return 0


def commandLint(args: argparse.Namespace, root: Path, logger, dryRun: bool) -> int:
    """Print the runLinter summary."""
    del args, dryRun
    snapshot = lintSnapshotLoad(root)
    print(snapshot.summary)
    for item in snapshot.findings:
        print(f"{item.path}: {item.ruleId} {item.message}")
    if logger is not None:
        logger.value("lint", snapshot.summary)
    return 1 if snapshot.findings else 0


def commandList(args: argparse.Namespace, root: Path, logger, dryRun: bool) -> int:
    """Print the board as text or JSON."""
    del dryRun
    board = boardLoad(root)
    if args.json:
        print(json.dumps(boardDump(board), indent=2))
        return 0
    print(gitContextLoad(root, board.release).summary())
    print(boardFormat(board), end="")
    if logger is not None:
        logger.value("requirements", len(board.cards))
    return 0


def commandMove(args: argparse.Namespace, root: Path, logger, dryRun: bool) -> int:
    """Move one requirement, writing only after confirmation."""
    plan = cardMove(root, args.number, args.column, dryRun=True)
    if not plan.changed:
        reportWrite(logger, plan.note)
        return 0
    changeReport(root, plan.changes, logger)
    if dryRun:
        reportWrite(logger, "dry-run left the files unchanged")
        return 0
    changeApply(plan.changes)
    if logger is not None:
        logger.value("column", plan.target)
    return 0


def commandPytest(args: argparse.Namespace, root: Path, logger, dryRun: bool) -> int:
    """Print the pytest summary."""
    del args, dryRun
    snapshot = pytestSnapshotLoad(root)
    print(snapshot.summary)
    if snapshot.text and snapshot.text != snapshot.summary:
        print(snapshot.text)
    if logger is not None:
        logger.value("pytest", snapshot.code)
    return 0 if snapshot.code == 0 else snapshot.code


def commandShow(args: argparse.Namespace, root: Path, logger, dryRun: bool) -> int:
    """Print one requirement, including linked branches and commits."""
    del dryRun
    board = boardLoad(root)
    card = board.cardGet(numberNormalise(args.number))
    print(cardFormat(card, requirementGitLoad(root, card.number)), end="")
    if logger is not None:
        logger.value("column", card.column)
    return 0


## utilities


def boardLaunch(args: argparse.Namespace) -> int:
    """Open the Textual board. Textual is imported only here."""
    try:
        from organiseMyProjects.myBoardTui import BoardApp
    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        if missing != "textual" and not missing.startswith("textual."):
            raise
        print(
            "myBoard needs Textual for the board.\n"
            "Install it with: pip install 'organiseMyProjects[tui]'\n"
            "list, show, move and create work without it.",
            file=sys.stderr,
        )
        return 2
    try:
        root = projectRootFind(args.project or Path.cwd())
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    BoardApp(root).run()
    return 0


def changeReport(root: Path, changes, logger) -> None:
    """Log each file a confirmed command would write."""
    for change in changes:
        if change.before == change.after:
            continue
        relative = change.path.relative_to(root).as_posix()
        if logger is None:
            print(relative)
        else:
            logger.action("write %s", relative)


def reportWrite(logger, message: str) -> None:
    """Print a narrative line, through the logger when a command has one."""
    if logger is None:
        print(message)
        return
    logger.info(message)


def _projectExtract(argv: list[str]) -> tuple[Path | None, list[str]]:
    """Lift ``--project`` out of the command line so it works in either position."""
    project = None
    cleaned = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--project" and index + 1 < len(argv):
            project = Path(argv[index + 1])
            index += 2
            continue
        if token.startswith("--project="):
            project = Path(token.split("=", 1)[1])
            index += 1
            continue
        cleaned.append(token)
        index += 1
    return project, cleaned


def columnParse(value: str) -> str:
    """Return a column name, using argparse's own type-error channel."""
    try:
        return columnNormalise(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _commandsAdd(
    parser: argparse.ArgumentParser, common: argparse.ArgumentParser
) -> None:
    commands = parser.add_subparsers(dest="command")
    listing = commands.add_parser(
        "list", parents=[common], help="List requirements by column."
    )
    listing.add_argument("--json", action="store_true", help="Print the board as JSON.")
    show = commands.add_parser("show", parents=[common], help="Show one requirement.")
    show.add_argument("number", help="Requirement number, for example 012.")
    move = commands.add_parser(
        "move", parents=[common], help="Move a requirement to a column."
    )
    move.add_argument("number", help="Requirement number, for example 012.")
    move.add_argument(
        "column", type=columnParse, help="Backlog, ToDo, InProgress or Completed."
    )
    _confirmAdd(move)
    _createAdd(commands, common)
    _editAdd(commands, common)
    check = commands.add_parser(
        "check", parents=[common], help="Show manageProject check findings."
    )
    check.add_argument("number", nargs="?", help="Limit findings to one requirement.")
    commands.add_parser(
        "lint", parents=[common], help="Run runLinter and print the summary."
    )
    commands.add_parser(
        "pytest", parents=[common], help="Run pytest and print the summary."
    )


def _commonParser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--project",
        type=Path,
        help="Project root. Defaults to the nearest project above the current directory.",
    )
    return common


def _confirmAdd(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-y",
        "--confirm",
        action="store_true",
        help="Write the change. The default is a dry-run.",
    )


def _createAdd(
    commands: argparse._SubParsersAction, common: argparse.ArgumentParser
) -> None:
    create = commands.add_parser(
        "create", parents=[common], help="Create the next requirement in the backlog."
    )
    create.add_argument(
        "--name", required=True, help="camelCase filename name, such as myBoard."
    )
    create.add_argument("--title", required=True, help="Requirement title.")
    create.add_argument("--description", required=True, help="One index sentence.")
    create.add_argument("--outcome", required=True, help="Outcome section.")
    create.add_argument("--context", default="", help="Context section.")
    create.add_argument("--scope", default="", help="Scope section.")
    create.add_argument("--excluded", default="", help="Out of scope section.")
    create.add_argument("--acceptance", default="", help="Acceptance criteria section.")
    create.add_argument("--verification", default="", help="Verification section.")
    _confirmAdd(create)


def _editAdd(
    commands: argparse._SubParsersAction, common: argparse.ArgumentParser
) -> None:
    edit = commands.add_parser(
        "edit", parents=[common], help="Edit requirement metadata and prose."
    )
    edit.add_argument("number", help="Requirement number, for example 012.")
    edit.add_argument("--title", help="Replacement requirement title.")
    edit.add_argument("--description", help="Replacement index description.")
    edit.add_argument("--outcome", help="Replacement Outcome section.")
    edit.add_argument("--context", help="Replacement Context section.")
    edit.add_argument("--scope", help="Replacement Scope section.")
    edit.add_argument("--excluded", help="Replacement Out of scope section.")
    edit.add_argument("--acceptance", help="Replacement Acceptance criteria section.")
    edit.add_argument(
        "--dependencies", help="Replacement Dependencies and decisions section."
    )
    edit.add_argument("--verification", help="Replacement Verification section.")
    _confirmAdd(edit)


if __name__ == "__main__":
    sys.exit(main())
