#!/usr/bin/env python3
"""CLI entry point for the GUI Naming Linter."""

import argparse
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from organiseMyProjects.fixMarkup import markupFix
from organiseMyProjects.guiNamingLinter import fileCheck, findingDescribe
from organiseMyProjects.logUtils import line, runStart, setApplication
from organiseMyProjects.version import VERSION

AUXILIARY_SOURCE_DIRS = ("ui", "qt", "tests")
SKIP_PACKAGE_DIR_NAMES = frozenset(
    {
        "build",
        "dist",
        "docs",
        "documentation",
        "examples",
        "output",
        "project",
        "qt",
        "scripts",
        "site-packages",
        "tests",
        "ui",
    }
)

# Compatibility allowances. Keep these narrow so genuinely new naming
# violations still surface; approved logging tokens live in guiNamingLinter.
LOGGING_VARIABLE_METHODS_ALLOWED = frozenset(
    {"action", "debug", "doing", "done", "error", "multiline", "warning"}
)
LOGGING_MESSAGE_ALLOWLIST = frozenset(
    {
        "Failed to restore terminal state after single-key prompt: %s",
        "could not merge %s into %s: %s",
        "could not rename TV show folder %s: %s",
        "could not rename movie folder %s: %s",
        "failed downloading %s: %s",
        "failed to rename %s: %s",
        "no TV storage locations available for type switch",
        "no movie storage locations available for type switch",
        "rescan TV show target already exists: %s",
        "rescan movie folder target already exists: %s",
        "rescan movie target already exists: %s",
        "rescan target already exists: %s",
    }
)
FUNCTION_NAME_ALLOWLIST = frozenset(
    {
        "_digest",
        "_mp4BoxIterate",
        "_mp4MvhdCreationRead",
        "_sha256",
    }
)
IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "output",
    }
)


def _tomlSectionBody(text: str, header: str) -> str:
    """Return the body of a TOML table, or an empty string when absent."""
    escaped = re.escape(header)
    match = re.search(rf"(?ms)^\[{escaped}\]\s*\n(.*?)(?=^\[|\Z)", text)
    return match.group(1) if match else ""


def _tomlQuotedList(body: str, key: str) -> list[str]:
    """Return a TOML array of quoted strings for ``key``."""
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\[([^\]]*)\]", body)
    if match is None:
        return []
    quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', match.group(1))
    return [item[0] or item[1] for item in quoted]


def _tomlQuotedString(body: str, key: str) -> str | None:
    """Return a quoted TOML string value for ``key``."""
    match = re.search(
        rf"(?m)^{re.escape(key)}\s*=\s*[\"']([^\"']+)[\"']",
        body,
    )
    return match.group(1) if match else None


def _tomlQuotedAssignments(body: str) -> dict[str, str]:
    """Return quoted key/value assignments from a TOML table body."""
    assignments: dict[str, str] = {}
    for match in re.finditer(
        r"(?m)^(\"(?:[^\"]*)\"|'(?:[^']*)'|[A-Za-z0-9_.-]+)\s*=\s*[\"']([^\"']*)[\"']",
        body,
    ):
        key = match.group(1).strip("\"'")
        assignments[key] = match.group(2)
    return assignments


def _childPythonPackages(root: Path) -> list[Path]:
    """Return immediate child directories that look like Python packages."""
    packages: list[Path] = []
    if not root.is_dir():
        return packages
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name in SKIP_PACKAGE_DIR_NAMES:
            continue
        hasInit = (child / "__init__.py").is_file()
        hasPython = next(child.glob("*.py"), None) is not None
        if hasInit or hasPython:
            packages.append(child)
    return packages


def _pyprojectSourceDirectories(root: Path) -> list[Path]:
    """Return source directories declared by setuptools packaging metadata."""
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return []

    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return []

    directories: list[Path] = []
    packageDir = _tomlQuotedAssignments(
        _tomlSectionBody(text, "tool.setuptools.package-dir")
    )
    rootMapping = packageDir.get("")
    if rootMapping not in {None, "", "."}:
        mappedRoot = root / rootMapping
        directories.append(mappedRoot)

    findBody = _tomlSectionBody(text, "tool.setuptools.packages.find")
    whereEntries = _tomlQuotedList(findBody, "where")
    if findBody and not whereEntries:
        whereEntries = ["."]
    for where in whereEntries:
        if where in {"", "."}:
            directories.extend(_childPythonPackages(root))
            continue
        directories.append(root / where)

    setuptoolsBody = _tomlSectionBody(text, "tool.setuptools")
    for packageName in _tomlQuotedList(setuptoolsBody, "packages"):
        mapped = packageDir.get(packageName, packageName)
        if mapped in {"", "."}:
            continue
        directories.append(root / mapped)

    projectName = _tomlQuotedString(_tomlSectionBody(text, "project"), "name")
    if projectName:
        mapped = packageDir.get(projectName, projectName)
        if mapped not in {"", "."}:
            directories.append(root / mapped)

    return directories


def _uniqueExistingDirectories(paths: list[Path], root: Path) -> list[str]:
    """Return existing unique directories as root-relative posix paths."""
    unique: list[str] = []
    seen: set[Path] = set()
    rootResolved = root.resolve()
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not path.is_dir():
            continue
        if resolved in seen:
            continue
        if resolved == rootResolved:
            continue
        seen.add(resolved)
        try:
            unique.append(resolved.relative_to(rootResolved).as_posix())
        except ValueError:
            unique.append(str(path))
    return unique


def lintTargetsDiscover(root: Path | None = None) -> list[str]:
    """Return default lint targets for a project root.

    Explicit CLI targets are not handled here. Discovery is deterministic and
    prefers packaging metadata over a whole-repository walk.
    """
    projectRoot = Path(root or Path.cwd()).resolve()
    candidates: list[Path] = []
    candidates.extend(_pyprojectSourceDirectories(projectRoot))

    namedPackage = projectRoot / projectRoot.name
    if namedPackage.is_dir():
        candidates.append(namedPackage)

    srcDir = projectRoot / "src"
    if srcDir.is_dir():
        candidates.append(srcDir)

    for name in AUXILIARY_SOURCE_DIRS:
        auxiliary = projectRoot / name
        if auxiliary.is_dir():
            candidates.append(auxiliary)

    discovered = _uniqueExistingDirectories(candidates, projectRoot)
    if discovered:
        return discovered
    return ["."]


def _violationAllowed(name: str, ruleType: str) -> bool:
    """Return whether a finding is an acknowledged OMP 0.8 compatibility case."""
    if ruleType == "Function name (domainAction)":
        return name in FUNCTION_NAME_ALLOWLIST

    if ruleType == "Logging variables (only logger.info/logger.value accept variables)":
        return name in LOGGING_VARIABLE_METHODS_ALLOWED

    # Approved tokens are validated exactly by guiNamingLinter; only these
    # specific historical messages remain allowed wholesale.
    if ruleType in {"Logging (info)", "Logging (warning)", "Logging (error)"}:
        return name in LOGGING_MESSAGE_ALLOWLIST

    return False


def _violationsFiltered(path: str) -> list[tuple[str, str, int]]:
    """Return linter findings excluding acknowledged compatibility cases."""
    return [item for item in fileCheck(path) if not _violationAllowed(item[0], item[1])]


EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2
EXIT_NO_FILES = 5


@dataclass(frozen=True)
class LintFinding:
    """One reportable finding at a file location."""

    path: str
    line: int
    ruleId: str
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.ruleId} {self.message}"


@dataclass
class LintResult:
    """Collected outcome of a lint run, independent of how it is printed."""

    files: list[str] = field(default_factory=list)
    findings: list[LintFinding] = field(default_factory=list)
    targetProblems: list[str] = field(default_factory=list)

    @property
    def failedFiles(self) -> list[str]:
        failed = {finding.path for finding in self.findings}
        return [path for path in self.files if path in failed]

    @property
    def exitCode(self) -> int:
        if self.targetProblems:
            return EXIT_USAGE
        if self.findings:
            return EXIT_FINDINGS
        if not self.files:
            return EXIT_NO_FILES
        return EXIT_OK


def _pathDisplay(path: str) -> str:
    """Return a path relative to the invocation directory where possible."""
    relative = os.path.relpath(path)
    return path if relative.startswith("..") else relative


def _pythonFilesIterate(target: str):
    """Yield Python files for a file or directory target in stable order."""
    if not os.path.isdir(target):
        yield target
        return
    for root, directories, files in os.walk(target):
        directories[:] = sorted(
            item for item in directories if item not in IGNORED_DIRECTORIES
        )
        for filename in sorted(files):
            if filename.endswith(".py"):
                yield os.path.join(root, filename)


def _targetProblem(target: str) -> str | None:
    """Describe why a supplied target cannot be linted, or None when usable."""
    if not os.path.exists(target):
        return f"target '{target}' does not exist"
    if not os.access(target, os.R_OK):
        return f"target '{target}' is not readable"
    if not os.path.isdir(target) and not target.endswith(".py"):
        return f"target '{target}' is not a Python file or directory"
    return None


def _fileFindings(path: str) -> list[LintFinding]:
    """Lint one file and describe each finding with a rule identifier."""
    display = _pathDisplay(path)
    try:
        violations = _violationsFiltered(path)
    except (SyntaxError, UnicodeDecodeError) as exc:
        lineNumber = getattr(exc, "lineno", None) or 1
        return [LintFinding(display, lineNumber, "LINT-001", f"cannot parse: {exc}")]
    findings = []
    for name, ruleType, lineNumber in violations:
        ruleId, message = findingDescribe(name, ruleType)
        findings.append(LintFinding(display, max(lineNumber, 1), ruleId, message))
    return findings


def lintTargetsCollect(targets: list[str], checkTargets: bool = True) -> LintResult:
    """Collect findings for targets without printing anything."""
    result = LintResult()
    seen = set()
    for target in targets:
        problem = _targetProblem(target) if checkTargets else None
        if problem:
            result.targetProblems.append(problem)
            continue
        for path in _pythonFilesIterate(target):
            display = _pathDisplay(path)
            if display in seen:
                continue
            seen.add(display)
            result.files.append(display)
            result.findings.extend(_fileFindings(path))
    return result


def _countPlural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def _bannerFormat(text: str, fill: str = "=") -> str:
    width = shutil.get_terminal_size((80, 24)).columns
    return f" {text} ".center(width, fill)


def _summaryText(result: LintResult, elapsed: float) -> str:
    duration = f"in {elapsed:.2f}s"
    passedCount = len(result.files) - len(result.failedFiles)
    parts = []
    if result.findings:
        parts.append(
            f"{_countPlural(len(result.findings), 'finding')} in "
            f"{_countPlural(len(result.failedFiles), 'file')}"
        )
    if passedCount:
        parts.append(f"{_countPlural(passedCount, 'file')} passed")
    if result.targetProblems:
        parts.append(_countPlural(len(result.targetProblems), "target error"))
    if not result.files and not result.targetProblems:
        parts.append("no Python files linted")
    return f"{', '.join(parts)} {duration}"


def lintReportPrint(
    result: LintResult, targets: list[str], elapsed: float, rootDir: str
) -> None:
    """Print a pytest-style report for a collected lint result."""
    print(f"rootdir: {rootDir}")
    print(f"targets: {', '.join(targets) if targets else '(none)'}")
    print()

    failed = set(result.failedFiles)
    for path in result.files:
        print(f"{path} {'FAILED' if path in failed else 'PASSED'}")

    if result.targetProblems:
        print()
        print(_bannerFormat("ERRORS"))
        for problem in result.targetProblems:
            print(f"ERROR: {problem}")

    if result.findings:
        print()
        print(_bannerFormat("FINDINGS"))
        for finding in result.findings:
            print(finding.render())

    print(_bannerFormat(_summaryText(result, elapsed)))


def main() -> None:

    parser = argparse.ArgumentParser(
        description="Run GUI naming linting and optional markup linting"
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="File or directory to lint; defaults to the current project",
    )
    parser.add_argument(
        "--markup",
        action="store_true",
        help="Run markdown lint checks using markdownlint-cli",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="With --markup, apply automatic markup fixes where possible",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="With --markup, enable strict markdown rules and report findings as warnings",
    )
    parser.add_argument(
        "--fix-markup",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.fix and not args.markup:
        parser.error("--fix requires --markup")
    if args.strict and not args.markup:
        parser.error("--strict requires --markup")

    setApplication("runLinter")
    runStart()
    print(f"organiseMyProjects runLinter {VERSION}")
    line()

    # Markup mode is intentionally isolated so markdown checks can be run
    # without triggering Python GUI naming lint.
    if args.markup or args.fix_markup:
        fixMode = bool(args.fix or args.fix_markup)
        markupExitCode = markupFix(
            targets=args.targets or None,
            fix=fixMode,
            strict=args.strict,
        )
        if markupExitCode != 0:
            raise SystemExit(markupExitCode)
        return

    started = time.perf_counter()
    if args.targets:
        targets = list(args.targets)
        result = lintTargetsCollect(targets)
    else:
        targets = lintTargetsDiscover()
        result = lintTargetsCollect(targets, checkTargets=False)
    lintReportPrint(result, targets, time.perf_counter() - started, os.getcwd())
    line()
    raise SystemExit(result.exitCode)


if __name__ == "__main__":
    main()
