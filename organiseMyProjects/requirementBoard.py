"""Load and update the requirement board for one OMP project.

The board is a view of the project it is run from. Each requirement appears
in one column:

- Backlog: status ToDo and not listed on the current increment
- ToDo: status ToDo and listed on the current increment
- InProgress: status InProgress
- Completed: status Completed

A confirmed move writes the requirement record, ``requirementsIndex.md`` and
``project/currentIncrement.md`` together. Git, pytest, runLinter and
``manageProject --check`` stay read-only signals. They never change a column.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

COLUMNS = ("Backlog", "ToDo", "InProgress", "Completed")
STATUSES = ("ToDo", "InProgress", "Completed")

_NAME = re.compile(r"^[a-z][A-Za-z0-9]*$")
# Spaces only. A newline must stay in place so the following blank line survives.
_NEXT_NUMBER = re.compile(r"(?m)^(Next available number:\s*)(\d+)[ \t]*$")
_FEATURE_LINK = re.compile(r"features/(\d{3})-")
# File paths in pytest output and in a requirement's Verification section.
_PYTEST_PATH = re.compile(r"(?<![\w.-])((?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]+)")
_HEADING = re.compile(r"(?m)^## ([^\n]+)\n")
_STATUS_WORD = re.compile(r"(—\s*)(ToDo|InProgress|Completed)\b")
# The feature-record template order, used to place a section an edit adds.
_RECORD_SECTIONS = (
    "Status",
    "Outcome",
    "Context",
    "Scope",
    "Out of scope",
    "Acceptance criteria",
    "Dependencies and decisions",
    "Verification",
    "Change history",
)
_RECORD_STATUS = re.compile(r"^## Status\s*\n+([A-Za-z]+)", re.M)
_RECORD_TITLE = re.compile(r"^# \d{3}:\s*(.+)$")
_VERSION = re.compile(r'^VERSION\s*=\s*["\']([^"\']+)["\']', re.M)


@dataclass(frozen=True)
class RequirementCard:
    """One requirement placed in a single board column."""

    number: str
    title: str
    description: str
    status: str
    indexStatus: str
    filename: str
    outcome: str
    onIncrement: bool
    inBacklog: bool
    verification: str

    @property
    def column(self) -> str:
        """Return the column this record occupies."""
        return cardColumn(self.status, self.onIncrement)

    @property
    def drift(self) -> bool:
        """Return whether the index status disagrees with the record."""
        return bool(self.indexStatus) and self.indexStatus != self.status


@dataclass(frozen=True)
class Board:
    """Requirements loaded from one project root."""

    root: Path
    release: str
    nextNumber: str
    cards: tuple[RequirementCard, ...]

    def cardGet(self, number: str) -> RequirementCard:
        """Return the card for a three-digit requirement number."""
        normalised = numberNormalise(number)
        for card in self.cards:
            if card.number == normalised:
                return card
        raise ValueError(f"requirement {normalised} is not on the board")


@dataclass(frozen=True)
class TextChange:
    """One file a move or create would replace."""

    path: Path
    before: str
    after: str


@dataclass(frozen=True)
class MoveResult:
    """The documents a column move would write."""

    number: str
    source: str
    target: str
    changes: tuple[TextChange, ...]
    note: str

    @property
    def changed(self) -> bool:
        """Return whether any document would differ."""
        return bool(self.changes)


@dataclass(frozen=True)
class CreateResult:
    """The documents a new requirement would add."""

    number: str
    filename: str
    changes: tuple[TextChange, ...]
    note: str

    @property
    def changed(self) -> bool:
        """Return whether any document would differ."""
        return bool(self.changes)


@dataclass(frozen=True)
class RequirementUpdate:
    """The editable metadata and prose fields for one requirement."""

    title: str | None = None
    description: str | None = None
    outcome: str | None = None
    context: str | None = None
    scope: str | None = None
    excluded: str | None = None
    acceptance: str | None = None
    dependencies: str | None = None
    verification: str | None = None


@dataclass(frozen=True)
class UpdateResult:
    """The documents an edit would replace."""

    number: str
    changes: tuple[TextChange, ...]
    note: str

    @property
    def changed(self) -> bool:
        """Return whether any document would differ."""
        return bool(self.changes)


@dataclass(frozen=True)
class CheckFinding:
    """One read-only check or lint finding."""

    ruleId: str
    severity: str
    message: str
    path: str


@dataclass(frozen=True)
class BranchVersion:
    """One unmerged branch and the OMP version stored on it."""

    name: str
    version: str | None


@dataclass(frozen=True)
class GitContext:
    """Branch state for the project, shown on the board strip."""

    available: bool
    branch: str
    dirty: bool
    aheadMain: int | None
    behindMain: int | None
    releaseBranch: str
    aheadRelease: int | None
    behindRelease: int | None
    openBranches: tuple[BranchVersion, ...] = ()

    def summary(self) -> str:
        """Return the one-line strip for this checkout."""
        return " | ".join(gitContextLines(self))


@dataclass(frozen=True)
class RequirementGit:
    """Branches, commits and paths linked to one requirement id."""

    branches: tuple[str, ...]
    commits: tuple[tuple[str, str], ...]
    paths: tuple[str, ...]


@dataclass(frozen=True)
class LintSnapshot:
    """A runLinter result for the project."""

    summary: str
    findings: tuple[CheckFinding, ...]


@dataclass(frozen=True)
class CommandSnapshot:
    """A pytest run, reduced to the lines the board can show."""

    code: int
    summary: str
    text: str


@dataclass(frozen=True)
class RequirementDraft:
    """The fields needed to capture one new requirement."""

    name: str
    title: str
    description: str
    outcome: str
    context: str = ""
    scope: str = ""
    excluded: str = ""
    acceptance: str = ""
    verification: str = ""


## board


def projectRootFind(start: Path) -> Path:
    """Return the nearest project root that owns a requirements index.

    Search starts at ``start`` and walks parents. The root is the directory
    that contains ``project/requirements/requirementsIndex.md``, which may be
    narrower than the Git repository.
    """
    current = start.resolve()
    if current.is_file():
        current = current.parent
    candidates = [current, *current.parents]
    for candidate in candidates:
        index = candidate / "project" / "requirements" / "requirementsIndex.md"
        if index.is_file():
            return candidate
    raise FileNotFoundError(
        f"no project/requirements/requirementsIndex.md at or above {start}"
    )


def boardLoad(root: Path) -> Board:
    """Read the requirement index, records and current increment."""
    root = root.resolve()
    indexPath = root / "project" / "requirements" / "requirementsIndex.md"
    indexText = _textRead(indexPath)
    incrementPath = root / "project" / "currentIncrement.md"
    incrementText = _textRead(incrementPath) if incrementPath.is_file() else ""
    rows = {row.number: row for row in _indexRows(indexText)}
    mentioned = _incrementIds(incrementText)
    cards = []
    features = root / "project" / "requirements" / "features"
    if features.is_dir():
        for path in sorted(features.glob("*.md")):
            number = path.name[:3]
            if not number.isdigit():
                continue
            title, status, outcome, verification = _recordRead(path)
            row = rows.get(number)
            cards.append(
                RequirementCard(
                    number=number,
                    title=title,
                    description=row.description if row else "",
                    status=status,
                    indexStatus=row.status if row else "",
                    filename=path.name,
                    outcome=outcome,
                    onIncrement=number in mentioned[0],
                    inBacklog=number in mentioned[1],
                    verification=verification,
                )
            )
    return Board(
        root=root,
        release=_releaseName(incrementText),
        nextNumber=_nextNumber(indexText),
        cards=tuple(cards),
    )


def boardDump(board: Board) -> list[dict[str, object]]:
    """Return the board as plain data for ``--json``."""
    return [
        {
            "number": card.number,
            "title": card.title,
            "column": card.column,
            "status": card.status,
            "indexStatus": card.indexStatus,
            "drift": card.drift,
        }
        for card in board.cards
    ]


def boardFormat(board: Board) -> str:
    """Return the four columns as plain text."""
    blocks = []
    for column in COLUMNS:
        cards = [card for card in board.cards if card.column == column]
        lines = [f"{column} ({len(cards)})"]
        for card in cards:
            drift = " !" if card.drift else ""
            lines.append(f"  {card.number}  {card.title}{drift}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def cardColumn(status: str, onIncrement: bool) -> str:
    """Place a requirement in exactly one column.

    InProgress and Completed follow the record status. A ToDo requirement is
    on the increment or it is backlog. Any other status stays visible in
    Backlog, or in ToDo when the increment already lists it.
    """
    if status == "InProgress":
        return "InProgress"
    if status == "Completed":
        return "Completed"
    if onIncrement:
        return "ToDo"
    return "Backlog"


def cardFormat(
    card: RequirementCard,
    git: RequirementGit | None = None,
    findings: tuple[CheckFinding, ...] | None = None,
    lint: tuple[CheckFinding, ...] | None = None,
    pytestLines: tuple[str, ...] | None = None,
) -> str:
    """Return the detail text for one card."""
    return _partsText(detailParts(card, git, findings, lint, pytestLines))


def detailParts(
    card: RequirementCard,
    git: RequirementGit | None = None,
    findings: tuple[CheckFinding, ...] | None = None,
    lint: tuple[CheckFinding, ...] | None = None,
    pytestLines: tuple[str, ...] | None = None,
) -> list[tuple[str, str]]:
    """Return ``(role, text)`` pairs for one card.

    A commit's text is ``revision`` then tab then subject. A pair's text is
    the label, a tab, and the value. Each changed file is its own ``file`` part.
    """
    parts = [
        ("title", f"{card.number}  {card.title}"),
        ("pair", f"Column\t{card.column}"),
        ("pair", f"Status\t{card.status}"),
    ]
    if card.drift:
        parts.append(("pair", f"Index status\t{card.indexStatus}"))
    if card.description:
        parts.append(("prose", card.description))
    if card.outcome:
        parts.append(("prose", card.outcome))
    parts.extend(_gitParts(git))
    parts.extend(_findingParts("Checks", findings, "no findings for this requirement"))
    parts.extend(
        _findingParts("Lint", lint, "no findings in files changed on a linked branch")
    )
    parts.extend(_pytestParts(pytestLines))
    return parts


def columnNormalise(value: str) -> str:
    """Return the canonical column name."""
    match = {column.casefold(): column for column in COLUMNS}
    try:
        return match[value.strip().casefold()]
    except KeyError as exc:
        names = ", ".join(COLUMNS)
        raise ValueError(f"column must be one of {names}") from exc


def numberNormalise(value: str) -> str:
    """Return a requirement id as three digits."""
    digits = value.strip()
    if not digits.isdigit() or not 0 < int(digits) < 1000:
        raise ValueError(f"requirement number must be 1 to 999, not {value!r}")
    return f"{int(digits):03d}"


## create


def requirementCreate(
    root: Path,
    draft: RequirementDraft,
    dryRun: bool = True,
    today: str | None = None,
) -> CreateResult:
    """Allocate the next requirement id and stage its record, prompt and index row.

    The new card starts in Backlog: status ToDo, and not on the current
    increment. Nothing is written unless ``dryRun`` is false.
    """
    root = root.resolve()
    number, filename = _createIdentity(root, _draftCheck(draft))
    result = _createResult(
        root, draft, number, filename, today or date.today().isoformat()
    )
    if not dryRun:
        changeApply(result.changes)
    return result


## edit


def requirementUpdate(
    root: Path,
    number: str,
    update: RequirementUpdate,
    dryRun: bool = True,
    today: str | None = None,
) -> UpdateResult:
    """Plan, and optionally write, editable requirement metadata and prose.

    Requirement identity and lifecycle status deliberately remain outside this
    operation: use a move to change its column or status.
    """
    result = _updatePlan(
        root, number, _updateCheck(update), today or date.today().isoformat()
    )
    if not dryRun:
        changeApply(result.changes)
    return result


## move


def cardMove(
    root: Path,
    number: str,
    target: str,
    dryRun: bool = True,
    today: str | None = None,
) -> MoveResult:
    """Plan, and optionally write, a move of one requirement to ``target``.

    Backlog and ToDo both keep status ToDo. Moving between them changes the
    current increment only. InProgress and Completed change the record, the
    index and the increment bullet together.
    """
    result = _movePlan(root, number, target, today or date.today().isoformat())
    if not dryRun:
        changeApply(result.changes)
    return result


def changeApply(changes: tuple[TextChange, ...]) -> None:
    """Replace each planned file. New parents are created for new files."""
    for change in changes:
        if change.before == change.after:
            continue
        change.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = change.path.with_name(f".{change.path.name}.myBoard-tmp")
        temporary.write_text(change.after, encoding="utf-8")
        temporary.replace(change.path)


## signals


def checkFindingsLoad(root: Path) -> tuple[CheckFinding, ...]:
    """Run manageProject's repository checks and return the findings."""
    from organiseMyProjects.agentCheck import AgentCheckValidator

    report = AgentCheckValidator(root.resolve()).runAll()
    return tuple(
        CheckFinding(
            finding.ruleId,
            finding.severity.value,
            finding.message,
            "" if finding.filePath is None else str(finding.filePath),
        )
        for finding in report.findings
    )


def findingsSelect(
    findings: tuple[CheckFinding, ...] | None, card: RequirementCard
) -> tuple[CheckFinding, ...] | None:
    """Keep findings that name this requirement. ``None`` means checks have not run."""
    if findings is None:
        return None
    pattern = re.compile(rf"(^|[^0-9]){re.escape(card.number)}([^0-9]|$)")
    selected = []
    for item in findings:
        blob = f"{item.path}\n{item.message}"
        if card.filename in blob or pattern.search(blob):
            selected.append(item)
    return tuple(selected)


def gitContextLoad(root: Path, release: str = "") -> GitContext:
    """Read the checkout, dirty state, and ahead/behind counts."""
    branchRun = _gitRun(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if branchRun is None or branchRun.returncode != 0:
        return GitContext(False, "", False, None, None, "", None, None)
    statusRun = _gitRun(root, ["status", "--porcelain"])
    dirty = bool(statusRun and statusRun.returncode == 0 and statusRun.stdout.strip())
    mainCounts = _aheadBehind(root, "main")
    releaseBranch = f"release/{release}" if release else ""
    releaseCounts = _aheadBehind(root, releaseBranch) if releaseBranch else None
    return GitContext(
        available=True,
        branch=branchRun.stdout.strip(),
        dirty=dirty,
        aheadMain=None if mainCounts is None else mainCounts[0],
        behindMain=None if mainCounts is None else mainCounts[1],
        releaseBranch=releaseBranch,
        aheadRelease=None if releaseCounts is None else releaseCounts[0],
        behindRelease=None if releaseCounts is None else releaseCounts[1],
        openBranches=tuple(_openBranches(root)),
    )


def gitContextLines(context: GitContext) -> list[str]:
    """Return one concise display line for each useful Git context item."""
    if not context.available:
        return ["Git: unavailable"]
    state = "dirty" if context.dirty else "clean"
    lines = [f"Branch: {context.branch} ({state})"]
    if context.aheadMain is not None and context.behindMain is not None:
        lines.append(f"main: +{context.aheadMain} -{context.behindMain}")
    if context.releaseBranch:
        if context.aheadRelease is None or context.behindRelease is None:
            lines.append(f"{context.releaseBranch}: unavailable")
        else:
            lines.append(
                f"{context.releaseBranch}: +{context.aheadRelease} -{context.behindRelease}"
            )
    lines.extend(
        f"Open: {item.name} ({item.version or 'version unavailable'})"
        for item in context.openBranches
    )
    return lines


def lintSelect(
    findings: tuple[CheckFinding, ...] | None, paths: tuple[str, ...]
) -> tuple[CheckFinding, ...] | None:
    """Keep lint findings in files changed on a linked branch."""
    if findings is None:
        return None
    if not paths:
        return ()
    wanted = {path.lstrip("./") for path in paths}
    selected = []
    for item in findings:
        candidate = item.path.lstrip("./")
        if candidate in wanted or any(candidate.endswith(path) for path in wanted):
            selected.append(item)
    return tuple(selected)


def lintSnapshotLoad(root: Path) -> LintSnapshot:
    """Lint the project and return the summary plus each finding."""
    from organiseMyProjects.runLinter import lintTargetsCollect

    result = lintTargetsCollect([str(root.resolve())])
    findings = tuple(
        CheckFinding(item.ruleId, "FAILURE", item.message, item.path)
        for item in result.findings
    )
    summary = "lint clean" if not findings else f"lint {len(findings)} findings"
    return LintSnapshot(summary, findings)


def pytestSnapshotLoad(root: Path) -> CommandSnapshot:
    """Run pytest quietly and keep the short summary."""
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=line"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return CommandSnapshot(1, "pytest failed to start", str(exc))
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    summary = lines[-1] if lines else "pytest produced no output"
    if len(summary) > 160:
        summary = summary[:157] + "..."
    return CommandSnapshot(completed.returncode, summary, _pytestKeep(completed.stdout))


def pytestSelect(
    snapshot: CommandSnapshot | None,
    paths: tuple[str, ...],
    verification: str = "",
) -> tuple[str, ...] | None:
    """Return pytest lines that belong to this requirement.

    ``None`` means pytest has not run. A failure line is kept when it names a
    changed file or a path written in Verification. The suite summary stays on
    the strip, so one requirement does not show another's failures.
    """
    if snapshot is None:
        return None
    if snapshot.summary == "pytest failed to start":
        return (snapshot.summary,)
    wanted = _pytestWanted(paths, verification)
    return tuple(
        line for line in snapshot.text.splitlines() if _pytestLineMatches(line, wanted)
    )


def requirementGitLoad(root: Path, number: str) -> RequirementGit:
    """Find the branch and commits for one requirement id.

    A branch counts when its name contains the id, or when it contains an
    unmerged commit whose message does. The card then lists that branch and
    the commits from the mention through the branch tip.
    """
    normalised = numberNormalise(number)
    pattern = re.compile(rf"(^|[^0-9]){re.escape(normalised)}([^0-9]|$)")
    mentioned = _commitsMentioning(root, normalised)
    branches = _branchesFor(root, pattern, mentioned)
    commits = _commitsForCard(root, branches, mentioned)
    paths = _commitPaths(root, [revision for revision, _subject in commits])
    if not paths:
        paths = _changedPaths(root, branches)
    return RequirementGit(tuple(branches[:8]), tuple(commits), paths)


## utilities


def _aheadBehind(root: Path, base: str) -> tuple[int, int] | None:
    """Return (ahead, behind) for HEAD against ``base``, or None when absent."""
    if not base:
        return None
    probe = _gitRun(root, ["rev-parse", "--verify", "--quiet", base])
    if probe is None or probe.returncode != 0:
        return None
    counted = _gitRun(root, ["rev-list", "--left-right", "--count", f"{base}...HEAD"])
    if counted is None or counted.returncode != 0:
        return None
    try:
        left, right = counted.stdout.split()
        return int(right), int(left)
    except ValueError:
        return None


def _bodyAppend(body: str, line: str) -> str:
    """Append one line before the section's trailing blank lines."""
    if not line.endswith("\n"):
        line += "\n"
    core = body.rstrip("\n")
    if not core.strip():
        return "\n" + line
    return core + "\n" + line


def _bulletEnsure(
    body: str, token: str, present: bool, status: str, bullet: str
) -> str:
    """Add, update or remove the single increment bullet for one requirement."""
    lines = body.splitlines(keepends=True)
    found = False
    output: list[str] = []
    for line in lines:
        if token in line:
            found = True
            if present:
                output.append(_statusWord(line, status))
            continue
        output.append(line)
    if present and not found:
        extra = bullet if bullet.endswith("\n") else bullet + "\n"
        blanks: list[str] = []
        while output and output[-1].strip() == "":
            blanks.append(output.pop())
        if output and not output[-1].endswith("\n"):
            output[-1] += "\n"
        output.append(extra)
        output.extend(reversed(blanks))
    text = "".join(output)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _bulletLine(number: str, title: str, filename: str, status: str) -> str:
    safe = title.replace("[", "(").replace("]", ")")
    return f"- [{number}: {safe}](requirements/features/{filename}) — {status}\n"


def _branchNames(root: Path) -> list[str]:
    """Return local branch names, plus a remote only when it has no local branch."""
    listed = _gitRun(
        root,
        ["for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"],
    )
    if listed is None or listed.returncode != 0:
        return []
    names = [
        name for name in listed.stdout.splitlines() if name and name != "origin/HEAD"
    ]
    local = {name for name in names if not name.startswith("origin/")}
    return [
        name
        for name in names
        if not (name.startswith("origin/") and name.removeprefix("origin/") in local)
    ]


def _branchVersion(root: Path, branch: str, current: str) -> str | None:
    """Return the OMP package version stored at one branch revision."""
    path = root / "organiseMyProjects" / "version.py"
    if branch == current:
        try:
            shown = path.read_text(encoding="utf-8")
        except OSError:
            return None
    else:
        completed = _gitRun(root, ["show", f"{branch}:organiseMyProjects/version.py"])
        if completed is None or completed.returncode != 0:
            return None
        shown = completed.stdout
    match = _VERSION.search(shown)
    return None if match is None else match.group(1)


def _branchesContaining(root: Path, revision: str) -> list[str]:
    """Return local branches that contain one commit."""
    listed = _gitRun(
        root, ["branch", "--contains", revision, "--format=%(refname:short)"]
    )
    if listed is None or listed.returncode != 0:
        return []
    return [name.strip() for name in listed.stdout.splitlines() if name.strip()]


def _branchesFor(
    root: Path, pattern: re.Pattern[str], mentioned: list[tuple[str, str]]
) -> list[str]:
    """Return branches named for the id, or holding its unmerged commits."""
    linked = [name for name in _branchNames(root) if pattern.search(name)]
    for revision, _subject in mentioned:
        if _commitIn(root, revision, "main"):
            continue
        for name in _earliestBranches(root, _branchesContaining(root, revision)):
            if name not in linked:
                linked.append(name)
    current = _currentBranch(root)
    if current in linked:
        linked = [current, *[name for name in linked if name != current]]
    return linked


def _earliestBranches(root: Path, holders: list[str]) -> list[str]:
    """Keep the branch that introduced the commit, not branches that contain it later."""
    return [
        branch
        for branch in holders
        if not any(
            other != branch and _commitIn(root, other, branch) for other in holders
        )
    ]


def _commitIn(root: Path, revision: str, branch: str) -> bool:
    """Return whether ``revision`` is already contained in ``branch``."""
    probe = _gitRun(root, ["merge-base", "--is-ancestor", revision, branch])
    return probe is not None and probe.returncode == 0


def _commitPaths(root: Path, revisions: list[str]) -> tuple[str, ...]:
    """Return files touched by these commits, in first-seen order."""
    paths: list[str] = []
    for revision in revisions:
        diff = _gitRun(
            root, ["diff-tree", "--no-commit-id", "--name-only", "-r", revision]
        )
        if diff is None or diff.returncode != 0:
            continue
        paths.extend(name for name in diff.stdout.splitlines() if name)
    return tuple(dict.fromkeys(paths))


def _commitsForCard(
    root: Path, branches: list[str], mentioned: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    """Prefer the short span from the requirement commit to the branch tip."""
    for branch in branches:
        if branch.startswith("origin/"):
            continue
        span = _branchCommitsSinceMention(root, branch, mentioned)
        if span:
            return span[:8]
    return mentioned[:8]


def _branchCommitsSinceMention(
    root: Path, branch: str, mentioned: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    """Return commits from an unmerged mention to the branch tip.

    A long span is left alone so an old merged requirement does not list
    every later commit on the current branch.
    """
    for revision, _subject in mentioned:
        if _commitIn(root, revision, "main") or not _commitIn(root, revision, branch):
            continue
        counted = _gitRun(root, ["rev-list", "--count", f"{revision}^..{branch}"])
        if counted is None or counted.returncode != 0:
            continue
        try:
            span = int(counted.stdout.strip())
        except ValueError:
            continue
        if span == 0 or span > 8:
            continue
        logged = _gitRun(
            root,
            ["log", f"{revision}^..{branch}", "--pretty=format:%h%x09%s"],
        )
        return _parseLog(logged)
    return []


def _commitsMentioning(root: Path, number: str) -> list[tuple[str, str]]:
    """Return recent commits whose message names this requirement id."""
    logged = _gitRun(
        root,
        [
            "log",
            "--all",
            "-n",
            "8",
            "-E",
            f"--grep=(^|[^0-9]){number}([^0-9]|$)",
            "--pretty=format:%h%x09%s",
        ],
    )
    return _parseLog(logged)


def _currentBranch(root: Path) -> str:
    current = _gitRun(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if current is None or current.returncode != 0:
        return ""
    return current.stdout.strip()


def _openBranches(root: Path) -> list[BranchVersion]:
    """Return unmerged local and remote-only branches with their versions."""
    branches = [
        branch for branch in _branchNames(root) if not _commitIn(root, branch, "main")
    ]
    current = _currentBranch(root)
    if current in branches:
        branches = [current, *[branch for branch in branches if branch != current]]
    return [
        BranchVersion(branch, _branchVersion(root, branch, current))
        for branch in branches
    ]


def _parseLog(
    completed: subprocess.CompletedProcess[str] | None,
) -> list[tuple[str, str]]:
    if completed is None or completed.returncode != 0 or not completed.stdout.strip():
        return []
    commits = []
    for line in completed.stdout.splitlines():
        revision, separator, subject = line.partition("\t")
        if separator and subject:
            commits.append((revision, subject))
    return commits


def _changedPaths(root: Path, branches: list[str]) -> tuple[str, ...]:
    """Return files changed on linked local branches since they diverged from main."""
    if _gitRun(root, ["rev-parse", "--verify", "--quiet", "main"]) is None:
        return ()
    paths: list[str] = []
    for branch in branches:
        if branch.startswith("origin/"):
            continue
        diff = _gitRun(root, ["diff", "--name-only", f"main...{branch}"])
        if diff is None or diff.returncode != 0:
            continue
        paths.extend(name for name in diff.stdout.splitlines() if name)
    return tuple(dict.fromkeys(paths))


def _draftCheck(draft: RequirementDraft) -> str:
    """Return the camelCase name, or reject a draft that cannot be stored."""
    name = draft.name.strip()
    if not _NAME.fullmatch(name):
        raise ValueError(
            f"requirement name {draft.name!r} must be camelCase, such as myBoard"
        )
    for fieldName in ("title", "description", "outcome"):
        if not getattr(draft, fieldName).strip():
            raise ValueError(f"{fieldName} is required")
    if "|" in draft.description or "|" in draft.title:
        raise ValueError("title and description cannot contain '|'")
    return name


def _updateCheck(update: RequirementUpdate) -> RequirementUpdate:
    """Reject an edit without fields or values invalid in index cells."""
    fields = (
        "title",
        "description",
        "outcome",
        "context",
        "scope",
        "excluded",
        "acceptance",
        "dependencies",
        "verification",
    )
    if not any(getattr(update, field) is not None for field in fields):
        raise ValueError("at least one editable field is required")
    # Both values are written into one index table row; the title is also
    # the record heading and the link text of index and increment entries.
    for field, unsafe in (("title", "|[]"), ("description", "|")):
        value = getattr(update, field)
        if value is None:
            continue
        if not value.strip():
            raise ValueError(f"{field} cannot be empty")
        if "\n" in value or "\r" in value:
            raise ValueError(f"{field} must be a single line")
        if any(character in value for character in unsafe):
            listed = " or ".join(f"'{character}'" for character in unsafe)
            raise ValueError(f"{field} cannot contain {listed}")
    for field in fields[2:]:
        value = getattr(update, field)
        if value is not None and not value.strip():
            raise ValueError(f"{field} cannot be empty")
    return update


def _createIdentity(root: Path, name: str) -> tuple[str, str]:
    """Return the next requirement number and filename, or reject a collision."""
    board = boardLoad(root)
    if not board.nextNumber:
        raise ValueError("requirements index has no next available number")
    filename = f"{board.nextNumber}-{name}.md"
    featurePath = root / "project" / "requirements" / "features" / filename
    promptPath = root / "project" / "requirements" / "prompt" / filename
    if featurePath.exists() or promptPath.exists():
        raise ValueError(
            f"{filename} already exists; the index next number is {board.nextNumber}"
        )
    return board.nextNumber, filename


def _createResult(
    root: Path, draft: RequirementDraft, number: str, filename: str, today: str
) -> CreateResult:
    featurePath = root / "project" / "requirements" / "features" / filename
    promptPath = root / "project" / "requirements" / "prompt" / filename
    indexPath = root / "project" / "requirements" / "requirementsIndex.md"
    indexText = indexPath.read_text(encoding="utf-8")
    changes = (
        TextChange(featurePath, "", _recordBuild(draft, number, today)),
        TextChange(promptPath, "", _promptBuild(draft, number, filename)),
        TextChange(
            indexPath, indexText, _indexAppend(indexText, draft, number, filename)
        ),
    )
    return CreateResult(
        number=number,
        filename=filename,
        changes=changes,
        note=f"create {number} {draft.title} in Backlog",
    )


def _documentJoin(preamble: str, sections: list[tuple[str, str]]) -> str:
    parts = [preamble]
    for heading, body in sections:
        parts.append(f"## {heading}\n")
        parts.append(body)
    return "".join(parts)


def _documentSplit(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Split a Markdown document into a preamble and ``##`` sections.

    The slices are exact, so joining them reproduces the file.
    """
    matches = list(_HEADING.finditer(text))
    if not matches:
        return text, []
    preamble = text[: matches[0].start()]
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(1).rstrip("\r"), text[match.end() : end]))
    return preamble, sections


def _pytestKeep(stdout: str) -> str:
    """Keep pytest lines that name a file. The summary line is stored apart."""
    kept = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("FAILED ") or _PYTEST_PATH.search(stripped):
            kept.append(stripped)
    return "\n".join(kept)


def _pytestLineMatches(line: str, wanted: set[str]) -> bool:
    """Return whether a pytest line names one of this requirement's paths."""
    if not wanted:
        return False
    for token in _PYTEST_PATH.findall(line):
        candidate = token.lstrip("./")
        if candidate in wanted:
            return True
        if any(
            candidate.endswith("/" + path) or path.endswith("/" + candidate)
            for path in wanted
        ):
            return True
    return False


def _pytestParts(
    lines: tuple[str, ...] | None,
) -> list[tuple[str, str]]:
    """Return the pytest block for one card."""
    if lines is None:
        return [("muted", "pytest: not run")]
    if not lines:
        return [("muted", "pytest: no failures for this requirement")]
    return [("heading", "pytest"), *(("finding", line) for line in lines)]


def _pytestWanted(paths: tuple[str, ...], verification: str) -> set[str]:
    """Return changed files plus paths named in Verification."""
    wanted = {path.lstrip("./") for path in paths if path.strip()}
    wanted.update(token.lstrip("./") for token in _PYTEST_PATH.findall(verification))
    return wanted


def _findingParts(
    label: str, findings: tuple[CheckFinding, ...] | None, empty: str
) -> list[tuple[str, str]]:
    if findings is None:
        return [("muted", f"{label}: not run")]
    if not findings:
        return [("muted", f"{label}: {empty}")]
    parts = [("heading", label)]
    for item in findings:
        location = f"{item.path}: " if item.path else ""
        parts.append(
            ("finding", f"{location}{item.ruleId} {item.severity}: {item.message}")
        )
    return parts


def _gitParts(git: RequirementGit | None) -> list[tuple[str, str]]:
    """Return branch, commits, and one part per changed file."""
    if git is None:
        return [("muted", "Git: not loaded")]
    if not git.branches and not git.commits and not git.paths:
        return [("muted", "Git: no branch or commit mentions this requirement")]
    parts: list[tuple[str, str]] = []
    if git.branches:
        label = "Branch" if len(git.branches) == 1 else "Branches"
        parts.append(("pair", f"{label}\t{', '.join(git.branches)}"))
    if git.commits:
        parts.append(("heading", "Commits"))
        for revision, subject in git.commits:
            parts.append(("commit", f"{revision}\t{subject}"))
    if git.paths:
        parts.append(("heading", "Changed files"))
        parts.extend(("file", path) for path in git.paths)
    return parts


def _partLine(role: str, text: str) -> list[str]:
    """Return the plain lines for one detail part."""
    if role == "pair":
        label, _, value = text.partition("\t")
        return [f"{label}: {value}"]
    if role == "commit":
        revision, _, subject = text.partition("\t")
        return [f"  {revision}  {subject}"]
    if role == "file":
        return [f"  {text}"]
    if role == "heading":
        return [f"{text}:"]
    if role == "finding":
        return [f"  {text}"]
    return [text]


def _partsText(parts: list[tuple[str, str]]) -> str:
    """Join detail parts into the plain text used by the command."""
    lines: list[str] = []
    for role, text in parts:
        if role in {"prose", "heading", "muted"} and lines and lines[-1] != "":
            lines.append("")
        lines.extend(_partLine(role, text))
    return "\n".join(lines) + "\n"


def _gitRun(root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _historyNote(before: str, after: str) -> str:
    return f"status {before or 'unset'} -> {after} — myBoard."


def _incrementChange(
    root: Path, card: RequirementCard, target: str, status: str
) -> TextChange | None:
    path = root / "project" / "currentIncrement.md"
    if not path.is_file():
        if target in {"Backlog", "ToDo", "InProgress"}:
            raise ValueError("project/currentIncrement.md does not exist")
        return None
    text = path.read_text(encoding="utf-8")
    # Completed cards stay on the increment only when they were already there.
    onRequirements = target in {"ToDo", "InProgress"} or (
        target == "Completed" and card.onIncrement
    )
    updated = _membershipSet(
        text,
        card.number,
        card.filename,
        card.title,
        status,
        onRequirements=onRequirements,
        onBacklog=target == "Backlog",
    )
    if updated == text:
        return None
    return TextChange(path, text, updated)


def _incrementUpdate(
    root: Path, card: RequirementCard, title: str | None
) -> TextChange | None:
    """Keep an existing increment or backlog bullet aligned with a new title."""
    if title is None:
        return None
    path = root / "project" / "currentIncrement.md"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    label = f"[{card.number}: {title.strip()}]"
    pattern = re.compile(
        rf"\[{re.escape(card.number)}: [^\]]+\]"
        rf"(?=\(requirements/features/{re.escape(card.filename)}\))"
    )
    preamble, sections = _documentSplit(text)
    updated = [
        (
            heading,
            (
                pattern.sub(label, body)
                if heading in {"Requirements", "Backlog"}
                else body
            ),
        )
        for heading, body in sections
    ]
    updatedText = _documentJoin(preamble, updated)
    if updatedText == text:
        return None
    return TextChange(path, text, updatedText)


def _incrementIds(text: str) -> tuple[set[str], set[str]]:
    """Return requirement ids mentioned under Requirements and under Backlog."""
    _, sections = _documentSplit(text)
    requirements: set[str] = set()
    backlog: set[str] = set()
    for heading, body in sections:
        found = set(_FEATURE_LINK.findall(body))
        if heading == "Requirements":
            requirements |= found
        elif heading == "Backlog":
            backlog |= found
    return requirements, backlog


def _indexAppend(text: str, draft: RequirementDraft, number: str, filename: str) -> str:
    row = (
        f"| {number} | [{draft.title}](features/{filename}) | "
        f"{draft.description.strip()} | ToDo | [Prompt](prompt/{filename}) | "
        "Not required |"
    )
    lines = text.splitlines(keepends=True)
    insertAt = _indexInsertAt(lines)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.insert(insertAt, row + "\n")
    updated = "".join(lines)
    match = _NEXT_NUMBER.search(updated)
    if match is None:
        raise ValueError("requirements index has no next available number")
    following = f"{int(number) + 1:03d}"
    return _NEXT_NUMBER.sub(rf"\g<1>{following}", updated, count=1)


def _indexChange(root: Path, card: RequirementCard, status: str) -> TextChange | None:
    path = root / "project" / "requirements" / "requirementsIndex.md"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    needle = f"(features/{card.filename})"
    for index, line in enumerate(lines):
        if needle not in line or not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[3] == status:
            return None
        cells[3] = status
        ending = "\n" if line.endswith("\n") else ""
        lines[index] = "| " + " | ".join(cells) + " |" + ending
        return TextChange(path, text, "".join(lines))
    raise ValueError(f"requirements index has no row for {card.filename}")


def _indexUpdate(
    root: Path, card: RequirementCard, update: RequirementUpdate
) -> TextChange | None:
    """Update editable title and description cells in the matching index row."""
    if update.title is None and update.description is None:
        return None
    path = root / "project" / "requirements" / "requirementsIndex.md"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    needle = f"(features/{card.filename})"
    for index, line in enumerate(lines):
        if needle not in line or not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if update.title is not None:
            cells[1] = f"[{update.title.strip()}](features/{card.filename})"
        if update.description is not None:
            cells[2] = update.description.strip()
        ending = "\n" if line.endswith("\n") else ""
        updated = "| " + " | ".join(cells) + " |" + ending
        if updated == line:
            return None
        lines[index] = updated
        return TextChange(path, text, "".join(lines))
    raise ValueError(f"requirements index has no row for {card.filename}")


def _indexInsertAt(lines: list[str]) -> int:
    insertAt = None
    for index, line in enumerate(lines):
        if re.search(r"\]\(features/\d{3}-[^)]+\.md\)", line):
            insertAt = index + 1
    if insertAt is None:
        raise ValueError("requirements index has no requirement rows")
    return insertAt


def _indexRows(text: str) -> tuple[_IndexRow, ...]:
    rows = []
    for line in text.splitlines():
        linked = re.search(r"\]\(features/(\d{3}-[^)]+\.md)\)", line)
        if linked is None or not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        filename = linked.group(1)
        rows.append(
            _IndexRow(
                number=filename[:3],
                description=cells[2],
                status=cells[3],
                filename=filename,
            )
        )
    return tuple(rows)


def _listBody(text: str, fallback: str, numbered: bool) -> str:
    cleaned = text.strip() or fallback
    if cleaned.startswith("- ") or cleaned.startswith("1. "):
        return cleaned
    prefix = "1. " if numbered else "- "
    return prefix + cleaned


def _membershipSet(
    text: str,
    number: str,
    filename: str,
    title: str,
    status: str,
    onRequirements: bool,
    onBacklog: bool,
) -> str:
    preamble, sections = _documentSplit(text)
    names = [heading for heading, _body in sections]
    if onRequirements and "Requirements" not in names:
        sections.append(("Requirements", "\n"))
    if onBacklog and "Backlog" not in names:
        sections.append(("Backlog", "\n"))
    token = f"features/{number}-"
    bullet = _bulletLine(number, title, filename, status)
    updated = []
    for heading, body in sections:
        if heading == "Requirements":
            body = _bulletEnsure(body, token, onRequirements, status, bullet)
        elif heading == "Backlog":
            body = _bulletEnsure(body, token, onBacklog, status, bullet)
        updated.append((heading, body))
    return _documentJoin(preamble, updated)


def _movePlan(root: Path, number: str, target: str, today: str) -> MoveResult:
    root = root.resolve()
    board = boardLoad(root)
    normalised = numberNormalise(number)
    column = columnNormalise(target)
    card = board.cardGet(normalised)
    statusAfter = "ToDo" if column in {"Backlog", "ToDo"} else column
    if card.column == column and not card.drift:
        return MoveResult(
            normalised, card.column, column, (), f"{normalised} is already in {column}"
        )
    changes = []
    for builder in (
        lambda: _recordChange(root, card, statusAfter, today),
        lambda: _indexChange(root, card, statusAfter),
        lambda: _incrementChange(root, card, column, statusAfter),
    ):
        change = builder()
        if change is not None:
            changes.append(change)
    return MoveResult(
        number=normalised,
        source=card.column,
        target=column,
        changes=tuple(changes),
        note=f"move {normalised} from {card.column} to {column}",
    )


def _updatePlan(
    root: Path, number: str, update: RequirementUpdate, today: str
) -> UpdateResult:
    """Build the minimum coherent document changes for one requirement edit."""
    root = root.resolve()
    board = boardLoad(root)
    card = board.cardGet(numberNormalise(number))
    changes = []
    record = _recordUpdate(root, card, update, today)
    if record is not None:
        changes.append(record)
    index = _indexUpdate(root, card, update)
    if index is not None:
        changes.append(index)
    increment = _incrementUpdate(root, card, update.title)
    if increment is not None:
        changes.append(increment)
    return UpdateResult(
        number=card.number,
        changes=tuple(changes),
        note=f"edit {card.number} {update.title.strip() if update.title else card.title}",
    )


def _nextNumber(text: str) -> str:
    match = _NEXT_NUMBER.search(text)
    if match is None:
        return ""
    return f"{int(match.group(2)):03d}"


def _promptBuild(draft: RequirementDraft, number: str, filename: str) -> str:
    return (
        f"# {number}: Implement {draft.title}\n"
        "\n"
        f"Implement requirement {number},\n"
        f"[{draft.title}](../features/{filename}).\n"
        "The requirement is authoritative for scope and acceptance criteria.\n"
        "\n"
        "Verification: pytest, runLinter, and manageProject check.\n"
    )


def _recordBuild(draft: RequirementDraft, number: str, today: str) -> str:
    sections = (
        ("Status", "ToDo"),
        ("Outcome", draft.outcome.strip()),
        ("Context", draft.context.strip() or "Why this requirement exists."),
        (
            "Scope",
            _listBody(draft.scope, "Behaviour included in this requirement.", False),
        ),
        (
            "Out of scope",
            _listBody(
                draft.excluded,
                "Closely related behaviour deliberately excluded.",
                False,
            ),
        ),
        (
            "Acceptance criteria",
            _listBody(
                draft.acceptance,
                "Given the requirement, when it is read, then the outcome is testable.",
                True,
            ),
        ),
        ("Dependencies and decisions", "- None."),
        ("Verification", _listBody(draft.verification, "pytest", False)),
        ("Change history", f"- {today}: created — myBoard."),
    )
    return _sectionJoin(f"# {number}: {draft.title.strip()}", sections)


def _recordChange(
    root: Path, card: RequirementCard, status: str, today: str
) -> TextChange | None:
    path = root / "project" / "requirements" / "features" / card.filename
    text = path.read_text(encoding="utf-8")
    if card.status == status:
        return None
    preamble, sections = _documentSplit(text)
    updated, found = _statusSections(sections, card.status, status, today)
    if not found:
        raise ValueError(f"{card.filename} has no Status section")
    return TextChange(path, text, _documentJoin(preamble, updated))


def _recordRead(path: Path) -> tuple[str, str, str, str]:
    text = path.read_text(encoding="utf-8")
    first = text.split("\n", 1)[0].strip()
    titleMatch = _RECORD_TITLE.match(first)
    title = titleMatch.group(1).strip() if titleMatch else path.stem
    statusMatch = _RECORD_STATUS.search(text)
    status = statusMatch.group(1) if statusMatch else ""
    return (
        title,
        status,
        _sectionText(text, "Outcome"),
        _sectionText(text, "Verification"),
    )


def _recordUpdate(
    root: Path, card: RequirementCard, update: RequirementUpdate, today: str
) -> TextChange | None:
    """Update selected record sections and append one durable history entry."""
    path = root / "project" / "requirements" / "features" / card.filename
    text = path.read_text(encoding="utf-8")
    preamble, sections = _documentSplit(text)
    title = update.title.strip() if update.title is not None else card.title
    replacements = {
        "Outcome": update.outcome,
        "Context": update.context,
        "Scope": update.scope,
        "Out of scope": update.excluded,
        "Acceptance criteria": update.acceptance,
        "Dependencies and decisions": update.dependencies,
        "Verification": update.verification,
    }
    changed = update.title is not None and title != card.title
    present = {heading for heading, _body in sections}
    # A record created without an optional section gains it in template order.
    for heading, value in replacements.items():
        if value is not None and heading not in present:
            sections.insert(_sectionPosition(sections, heading), (heading, ""))
    updated = []
    for heading, body in sections:
        value = replacements.get(heading)
        if value is not None:
            replacement = "\n" + value.strip() + "\n\n"
            changed = changed or replacement.strip() != body.strip()
            body = replacement
        updated.append((heading, body))
    if not changed:
        return None
    history = f"- {today}: edited — myBoard.\n"
    found = False
    result = []
    for heading, body in updated:
        if heading == "Change history":
            body = _bodyAppend(body, history)
            found = True
        result.append((heading, body))
    if not found:
        result.append(("Change history", "\n" + history))
    # Added sections may follow what was the final section, so every heading
    # after the first must be preceded by a blank line.
    result = [
        (heading, body if body.endswith("\n\n") else body.rstrip("\n") + "\n\n")
        for heading, body in result[:-1]
    ] + result[-1:]
    # Only the heading line changes; any other preamble text is kept.
    first, newline, rest = preamble.partition("\n")
    if _RECORD_TITLE.match(first.strip()):
        preamble = f"# {card.number}: {title}" + newline + rest
    # A replaced final section must not leave extra blank lines at the end.
    return TextChange(path, text, _documentJoin(preamble, result).rstrip("\n") + "\n")


def _releaseName(text: str) -> str:
    _preamble, sections = _documentSplit(text)
    for heading, body in sections:
        if heading != "Increment":
            continue
        for line in body.splitlines():
            match = re.match(r"(\d+\.\d+(?:\.\d+)?)\b", line.strip())
            if match:
                return match.group(1)
    return ""


def _sectionJoin(title: str, sections: tuple[tuple[str, str], ...]) -> str:
    parts = [title, ""]
    for heading, body in sections:
        parts.extend([f"## {heading}", "", body, ""])
    return "\n".join(parts).rstrip() + "\n"


def _sectionPosition(sections: list[tuple[str, str]], heading: str) -> int:
    """Return where a missing record section belongs in template order."""
    rank = _RECORD_SECTIONS.index(heading)
    for position, (name, _body) in enumerate(sections):
        if name in _RECORD_SECTIONS and _RECORD_SECTIONS.index(name) > rank:
            return position
    return len(sections)


def _sectionText(text: str, heading: str) -> str:
    _preamble, sections = _documentSplit(text)
    for name, body in sections:
        if name == heading:
            return body.strip()
    return ""


def _statusSections(
    sections: list[tuple[str, str]], before: str, after: str, today: str
) -> tuple[list[tuple[str, str]], bool]:
    """Set the Status section and append a change-history line."""
    found = False
    history = False
    updated = []
    note = f"- {today}: {_historyNote(before, after)}\n"
    for heading, body in sections:
        if heading == "Status":
            body = _statusBody(body, after)
            found = True
        elif heading == "Change history":
            body = _bodyAppend(body, note)
            history = True
        updated.append((heading, body))
    if found and not history:
        updated.append(("Change history", "\n" + note))
    return updated, found


def _statusBody(body: str, status: str) -> str:
    match = re.search(r"[A-Za-z]+", body)
    if match is None:
        return f"\n{status}\n"
    return body[: match.start()] + status + body[match.end() :]


def _statusWord(line: str, status: str) -> str:
    if _STATUS_WORD.search(line):
        return _STATUS_WORD.sub(lambda match: match.group(1) + status, line, count=1)
    return line


def _textRead(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read {path}") from exc


@dataclass(frozen=True)
class _IndexRow:
    number: str
    description: str
    status: str
    filename: str
