"""Manifest-directed, read-only-first deployment of OMPR runtime helpers.

The canonical code remains in organiseMyProjects. Deployed copies are owned
only if they carry the explicit OMPR runtime marker; arbitrary consumer files
are never overwritten. No dependency on the toolkit is written to consumers.
"""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from organiseMyProjects.version import VERSION

RUNTIME_MANIFEST = ("logUtils.py", "logUtils.sh")
MARKER = "# OMPR-RUNTIME-MANAGED"
NAMESPACE = "ompr"


@dataclass(frozen=True)
class RuntimeChange:
    """One planned deployment action and its safety status."""

    path: Path
    action: str
    reason: str = ""


def runtimeContent(name: str, version: str = VERSION) -> str:
    """Build a provenance-marked copy of one manifest-listed source module."""
    if name not in RUNTIME_MANIFEST:
        raise ValueError(f"runtime module is not manifest-listed: {name}")
    source = Path(__file__).resolve().parent / name
    contents = source.read_text(encoding="utf-8")
    marker = (
        f"{MARKER} source=organiseMyProjects/{name} "
        f"version={version}; do not edit locally\n"
    )
    if contents.startswith("#!"):
        shebang, rest = contents.split("\n", 1)
        return shebang + "\n" + marker + rest
    return marker + contents


def _initContent(version: str) -> str:
    return (
        f"{MARKER} source=organiseMyProjects/runtimeSync.py "
        f"version={version}; do not edit locally\\n"
        '\"\"\"Synchronised OMPR runtime helpers.\"\"\"\\n'
    )


def _managed(text: str) -> bool:
    """Require the marker at the beginning, after an optional shebang."""
    lines = text.splitlines()
    if lines and lines[0].startswith("#!"):
        lines = lines[1:]
    return bool(lines and lines[0].startswith(MARKER + " source="))


def runtimePlan(project: Path, version: str = VERSION) -> tuple[RuntimeChange, ...]:
    """Plan changes without touching project content or following target links."""
    root = Path(project)
    if not root.is_dir():
        return (RuntimeChange(root, "blocked", "project directory does not exist"),)
    package = root / NAMESPACE
    if package.is_symlink() or (package.exists() and not package.is_dir()):
        return (RuntimeChange(package, "blocked", "runtime package is not a directory"),)

    init = package / "__init__.py"
    if package.exists() and not init.is_file():
        # A populated ompr directory without an ownership marker is not ours.
        if any(package.iterdir()):
            return (
                RuntimeChange(package, "blocked", "unowned ompr package exists"),
            )
    if init.is_file():
        if init.is_symlink():
            return (RuntimeChange(init, "blocked", "symbolic link is not managed"),)
        try:
            initText = init.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return (RuntimeChange(init, "blocked", "cannot read package ownership"),)
        if not _managed(initText):
            return (
                RuntimeChange(package, "blocked", "unowned ompr package exists"),
            )

    files = {"__init__.py": _initContent(version)}
    files.update({name: runtimeContent(name, version) for name in RUNTIME_MANIFEST})
    changes: list[RuntimeChange] = []
    for name, wanted in files.items():
        target = package / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            changes.append(RuntimeChange(target, "blocked", "non-file or symbolic link"))
            continue
        if target.is_file():
            try:
                current = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                changes.append(RuntimeChange(target, "blocked", "cannot read file"))
                continue
            if not _managed(current):
                changes.append(RuntimeChange(target, "blocked", "project-owned file"))
            elif current == wanted:
                changes.append(RuntimeChange(target, "unchanged"))
            else:
                changes.append(RuntimeChange(target, "update"))
        else:
            changes.append(RuntimeChange(target, "create"))
    return tuple(changes)


def runtimeSync(
    project: Path,
    *,
    dryRun: bool = True,
    report: Callable[[str], None] | None = None,
) -> tuple[RuntimeChange, ...]:
    """Synchronise a selected project, refusing ambiguous ownership.

    A blocked plan is wholly non-mutating: never partially install a package
    with only some modules. Every action is explicit and idempotent.
    """
    root = Path(project).expanduser().resolve()
    changes = runtimePlan(root)
    if report is not None:
        for change in changes:
            qualifier = f": {change.reason}" if change.reason else ""
            verb = change.action
            if dryRun and change.action in {"create", "update"}:
                verb = f"would {change.action}"
            report(f"runtime {verb}: {change.path}{qualifier}")
    if dryRun or any(change.action == "blocked" for change in changes):
        return changes
    package = root / NAMESPACE
    package.mkdir(parents=True, exist_ok=True)
    for change in changes:
        if change.action not in {"create", "update"}:
            continue
        if change.path.name == "__init__.py":
            wanted = _initContent(VERSION)
        else:
            wanted = runtimeContent(change.path.name)
        change.path.write_text(wanted, encoding="utf-8")
        if change.path.suffix == ".sh":
            mode = change.path.stat().st_mode
            change.path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return changes


def runtimeBatch(
    projects: list[Path],
    *,
    dryRun: bool = True,
    report: Callable[[str], None] | None = None,
) -> dict[str, tuple[RuntimeChange, ...]]:
    """Sync explicit local project selections without implicit filesystem scans."""
    results: dict[str, tuple[RuntimeChange, ...]] = {}
    for project in projects:
        root = Path(project).expanduser().resolve()
        results[str(root)] = runtimeSync(root, dryRun=dryRun, report=report)
    return results
