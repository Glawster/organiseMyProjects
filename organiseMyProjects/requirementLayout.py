"""OMP 0.6 requirement, prompt, and directory-index layout compatibility.

The migration is intentionally conservative. It recognises only known OMP
index shapes and deterministic per-requirement/per-prompt directory forms.
Arbitrary user-owned README files and multi-file directories are preserved.
"""

from __future__ import annotations

import re
from pathlib import Path

_INDEX_MIGRATIONS = (
    (
        Path("project/requirements/README.md"),
        Path("project/requirements/requirementsIndex.md"),
        ("# Requirements", "Next available number:"),
    ),
    (
        Path("project/requirements/folderIndex.md"),
        Path("project/requirements/requirementsIndex.md"),
        ("# Requirements", "Next available number:"),
    ),
    (
        Path("project/adr/README.md"),
        Path("project/adr/adrIndex.md"),
        ("# Architecture decision records",),
    ),
    (
        Path("project/adr/folderIndex.md"),
        Path("project/adr/adrIndex.md"),
        ("# Architecture decision records",),
    ),
)

_REFERENCE_REPLACEMENTS = (
    ("project/requirements/README.md", "project/requirements/requirementsIndex.md"),
    (
        "project/requirements/folderIndex.md",
        "project/requirements/requirementsIndex.md",
    ),
    ("project/adr/README.md", "project/adr/adrIndex.md"),
    ("project/adr/folderIndex.md", "project/adr/adrIndex.md"),
    ("requirements/README.md", "requirements/requirementsIndex.md"),
    ("requirements/folderIndex.md", "requirements/requirementsIndex.md"),
    ("adr/README.md", "adr/adrIndex.md"),
    ("adr/folderIndex.md", "adr/adrIndex.md"),
)

_REQUIREMENT_DIR_RE = re.compile(r"^(\d{3})-([A-Za-z][A-Za-z0-9_-]*)$")
# Any record name with a three-digit number, optionally behind a project prefix.
_REQUIREMENT_NAME_RE = re.compile(r"(?:[A-Za-z]+-)?(\d{3})-(.+)\.md")
_PROMPT_DIR_RE = re.compile(r"^(\d{3}[a-z]?)-([A-Za-z][A-Za-z0-9_-]*)$")

_IGNORED_GENERATED_DIRECTORIES = frozenset(
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


def _loggerAction(logger, message: str) -> None:
    if logger is not None:
        logger.action(message)


def _loggerInfo(logger, message: str) -> None:
    if logger is not None:
        logger.info(message)


def _textRead(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _indexRecognised(path: Path, markers: tuple[str, ...]) -> bool:
    text = _textRead(path)
    if text is None:
        return False

    folded = text.casefold()
    if not all(marker.casefold() in folded for marker in markers):
        return False

    if path.parent.name == "requirements":
        return (
            "## requirement index" in folded
            or re.search(r"\]\(features/\d{3}-[^)]+\.md\)", text) is not None
        )

    if path.parent.name == "adr":
        return (
            "## decision index" in folded
            or re.search(r"\]\(\d{3}-[^)]+\.md\)", text) is not None
        )

    return False


def requirementFilenameSuggest(name: str) -> str | None:
    """Return the conforming ``<nnn>-<camelCaseName>.md`` form of a record name.

    A leading project prefix such as ``MA-`` is dropped and a hyphenated or
    underscored name becomes camelCase. ``None`` means no number was found.
    """
    match = _REQUIREMENT_NAME_RE.fullmatch(name)
    if not match:
        return None
    number, words = match.group(1), re.split(r"[-_\s]+", match.group(2))
    words = [word for word in words if word]
    if not words:
        return None
    camel = (
        words[0][:1].lower()
        + words[0][1:]
        + "".join(word[:1].upper() + word[1:] for word in words[1:])
    )
    return f"{number}-{camel}.md"


def requirementNumber(name: str) -> str | None:
    """Return the three-digit number of a record name, ignoring any prefix."""
    match = _REQUIREMENT_NAME_RE.fullmatch(name)
    return match.group(1) if match else None


def pathGenerated(path: Path) -> bool:
    """Return whether a path is inside generated or transient project state."""
    return any(part in _IGNORED_GENERATED_DIRECTORIES for part in path.parts)


def _referencePathsIterate(basePath: Path):
    for path in basePath.rglob("*.md"):
        if pathGenerated(path):
            continue
        yield path


def _referencesUpdate(basePath: Path, dryRun: bool, logger) -> None:
    for path in _referencePathsIterate(basePath):
        text = _textRead(path)
        if text is None:
            continue
        updated = text
        for old, new in _REFERENCE_REPLACEMENTS:
            updated = updated.replace(f"]({old})", f"]({new})")
            updated = updated.replace(f"](<{old}>)", f"](<{new}>)")
        if updated == text:
            continue
        if dryRun:
            _loggerAction(logger, f"would update directory-index reference {path}")
        else:
            path.write_text(updated, encoding="utf-8")
            _loggerAction(logger, f"updated directory-index reference {path}")


def _indexMigrate(basePath: Path, dryRun: bool, logger) -> None:
    for oldRel, newRel, markers in _INDEX_MIGRATIONS:
        oldPath = basePath / oldRel
        newPath = basePath / newRel
        if not oldPath.is_file():
            continue
        if not _indexRecognised(oldPath, markers):
            _loggerInfo(
                logger,
                f"legacy index preserved because ownership is ambiguous: {oldPath}",
            )
            continue

        oldText = _textRead(oldPath)
        newText = _textRead(newPath) if newPath.is_file() else None
        if newText is not None and newText != oldText:
            scaffoldOnly = "Next available number: 001" in (
                oldText or ""
            ) and not re.search(r"^\|\s*\d{3}\s*\|", oldText or "", re.MULTILINE)
            if not scaffoldOnly:
                _loggerInfo(
                    logger,
                    f"directory index migration skipped because target exists: {newPath}",
                )
                continue

        if dryRun:
            verb = (
                "would remove obsolete index" if newText is not None else "would rename"
            )
            _loggerAction(logger, f"{verb} {oldPath} -> {newPath}")
            continue

        newPath.parent.mkdir(parents=True, exist_ok=True)
        if newText is None:
            oldPath.replace(newPath)
            _loggerAction(logger, f"renamed {oldPath} to {newPath}")
        else:
            oldPath.unlink()
            _loggerAction(logger, f"removed obsolete index {oldPath}")


def _directoryArtifactMigrate(
    parent: Path,
    namePattern: re.Pattern[str],
    dryRun: bool,
    logger,
    promptMode: bool = False,
) -> None:
    if not parent.is_dir():
        return

    for directory in sorted(path for path in parent.iterdir() if path.is_dir()):
        match = namePattern.fullmatch(directory.name)
        if match is None:
            continue
        entries = sorted(directory.iterdir())
        if promptMode:
            candidates = [
                entry
                for entry in entries
                if entry.is_file() and entry.suffix.casefold() == ".md"
            ]
        else:
            candidates = [
                entry for entry in entries if entry.name in {"README.md", "prompt.md"}
            ]
        if len(entries) != 1 or len(candidates) != 1:
            _loggerInfo(
                logger,
                f"legacy artifact directory preserved because contents are ambiguous: {directory}",
            )
            continue

        source = candidates[0]
        destination = parent / f"{directory.name}.md"
        sourceText = _textRead(source)
        if sourceText is None:
            continue

        if promptMode:
            requirementName = re.sub(r"^(\d{3})[a-z]-", r"\1-", directory.name)
            feature = parent.parent / "features" / f"{requirementName}.md"
            if not feature.is_file():
                _loggerInfo(
                    logger,
                    f"prompt directory preserved because requirement mapping is ambiguous: {directory}",
                )
                continue
        else:
            requirementNumber = match.group(1)
            if (
                re.search(
                    rf"^#\s+{re.escape(requirementNumber)}\s*:",
                    sourceText,
                    re.MULTILINE,
                )
                is None
            ):
                _loggerInfo(
                    logger,
                    f"requirement directory preserved because specification identity is ambiguous: {directory}",
                )
                continue

        if destination.exists():
            destinationText = _textRead(destination)
            if destinationText != sourceText:
                _loggerInfo(
                    logger,
                    f"legacy artifact migration skipped because target exists: {destination}",
                )
                continue

        if dryRun:
            _loggerAction(logger, f"would migrate {source} to {destination}")
            continue

        if not destination.exists():
            source.replace(destination)
            _loggerAction(logger, f"migrated {source} to {destination}")
        else:
            source.unlink()
            _loggerAction(logger, f"removed duplicate legacy artifact {source}")
        try:
            directory.rmdir()
            _loggerAction(logger, f"removed empty legacy directory {directory}")
        except OSError:
            pass


def legacyIndexFind(basePath: Path | str, newRel: Path | str) -> Path | None:
    """Return an existing legacy index that migrates to ``newRel``, if any."""
    root = Path(basePath)
    for oldRel, targetRel, _markers in _INDEX_MIGRATIONS:
        if targetRel == Path(newRel) and (root / oldRel).is_file():
            return root / oldRel
    return None


def layoutMigrate(basePath: Path | str, dryRun: bool = False, logger=None) -> None:
    """Apply requirement 004's deterministic layout migrations."""
    root = Path(basePath)
    if not root.exists():
        return

    _indexMigrate(root, dryRun, logger)
    _directoryArtifactMigrate(
        root / "project" / "requirements" / "features",
        _REQUIREMENT_DIR_RE,
        dryRun,
        logger,
    )
    _directoryArtifactMigrate(
        root / "project" / "requirements" / "prompt",
        _PROMPT_DIR_RE,
        dryRun,
        logger,
        promptMode=True,
    )
    _referencesUpdate(root, dryRun, logger)
