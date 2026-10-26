"""Requirement 016: correct non-conforming requirement and prompt names.

The correction is deterministic. A record keeps its number; a project prefix is
dropped and a hyphenated name becomes camelCase. Prompts move to
``project/requirements/prompt/`` beside the record they belong to. Markdown
links are rewritten; other mentions of old names or IDs are only reported,
because prose and code may quote them deliberately.

Nothing changes in dry-run mode, an existing destination is never overwritten,
and a corrected repository produces no further changes.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from organiseMyProjects.requirementLayout import (
    pathGenerated,
    requirementFilenameSuggest,
)

_PROMPT_NAME_RE = re.compile(r"(?:[A-Za-z]+-)?(\d{3})([a-z]?)-(.+)\.md")
_LEGACY_PROMPT_DIRS = (Path("project/prompts"),)
_LINK_RE = re.compile(r"(\]\()([^)\s]+)(\))")
_HEADING_RE = re.compile(r"\A#\s*(?:[A-Za-z]+-)?(\d{3})(?::|\s+-)?\s+(\S.*)")
_NOTE_TEXT = "name corrected to follow documentation/requirementsManagement.md"
_MENTION_SUFFIXES = (".md", ".py", ".toml", ".yml", ".yaml", ".txt", ".cfg")


@dataclass
class NamingCorrection:
    """What a correction run found, changed or left for review."""

    renames: dict[Path, Path] = field(default_factory=dict)
    edited: list[Path] = field(default_factory=list)
    collisions: list[str] = field(default_factory=list)
    # Sources whose rename collided; they are left entirely unchanged.
    blocked: set[Path] = field(default_factory=set)
    mentions: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.renames or self.edited)


## workflow


def requirementNamesCorrect(
    basePath: Path | str, dryRun: bool = True, logger=None
) -> NamingCorrection:
    """Rename records and prompts to the guide's form and rewrite links."""
    root = Path(basePath).resolve()
    result = NamingCorrection()
    featuresDir = root / "project" / "requirements" / "features"
    if not featuresDir.is_dir():
        return result

    # Work out every move first so links can be rewritten in one pass.
    _featureRenamesPlan(root, featuresDir, result)
    _promptRenamesPlan(root, result)
    contents = _contentsCorrect(root, result)
    _mentionsCollect(root, result, contents)

    for message in result.collisions + result.mentions:
        _loggerInfo(logger, message)
    for source, destination in result.renames.items():
        _loggerAction(
            logger,
            f"rename {_pathRelative(root, source)} to {_pathRelative(root, destination)}",
        )
    for path in result.edited:
        _loggerAction(logger, f"update names and links in {_pathRelative(root, path)}")
    if dryRun:
        return result

    # Write corrected text at the old location, then move it.
    for path, text in contents.items():
        path.write_text(text, encoding="utf-8")
    for source, destination in result.renames.items():
        _fileMove(root, source, destination)
    for legacy in _LEGACY_PROMPT_DIRS:
        _directoryRemoveEmpty(root / legacy, logger)
    return result


## planning


def _featureRenamesPlan(
    root: Path, featuresDir: Path, result: NamingCorrection
) -> None:
    for source in sorted(featuresDir.glob("*.md")):
        suggested = requirementFilenameSuggest(source.name)
        if suggested and suggested != source.name:
            _renameAdd(root, source, featuresDir / suggested, result)


def _promptRenamesPlan(root: Path, result: NamingCorrection) -> None:
    promptDir = root / "project" / "requirements" / "prompt"
    features = {
        destination.name[:3]: destination.stem
        for destination in _featureNames(root, result)
    }
    sources = sorted(promptDir.glob("*.md")) if promptDir.is_dir() else []
    for legacy in _LEGACY_PROMPT_DIRS:
        if (root / legacy).is_dir():
            sources += sorted((root / legacy).glob("*.md"))
    for source in sources:
        match = _PROMPT_NAME_RE.fullmatch(source.name)
        if not match:
            continue
        number, suffix, _name = match.groups()
        # A prompt follows its record's corrected name, keeping any a/b suffix.
        stem = features.get(number)
        if stem is None:
            suggested = requirementFilenameSuggest(f"{number}-{match.group(3)}.md")
            stem = Path(suggested).stem if suggested else source.stem
        name = f"{number}{suffix}-{stem.split('-', 1)[1]}.md"
        destination = promptDir / name
        if destination != source:
            _renameAdd(root, source, destination, result)


def _featureNames(root: Path, result: NamingCorrection) -> list[Path]:
    featuresDir = root / "project" / "requirements" / "features"
    return [result.renames.get(path, path) for path in sorted(featuresDir.glob("*.md"))]


def _renameAdd(
    root: Path, source: Path, destination: Path, result: NamingCorrection
) -> None:
    taken = destination.exists() or destination in result.renames.values()
    if taken:
        result.blocked.add(source)
        result.collisions.append(
            f"not renaming {_pathRelative(root, source)}: {_pathRelative(root, destination)} already exists"
        )
        return
    result.renames[source] = destination


## content


def _contentsCorrect(root: Path, result: NamingCorrection) -> dict[Path, str]:
    """Return corrected text for every file whose content changes."""
    moves = {
        source.resolve(): destination.resolve()
        for source, destination in result.renames.items()
    }
    contents: dict[Path, str] = {}
    for path in _textFiles(root, (".md",)):
        if path in result.blocked:
            continue
        original = path.read_text(encoding="utf-8")
        text = _linksRewrite(original, path.resolve(), moves)
        if path.parent.name == "features" and path.parent.parent.name == "requirements":
            text = _recordCorrect(text, path, result)
        elif path.name == "requirementsIndex.md":
            text = _indexIdsCorrect(text)
        if text != original:
            contents[path] = text
            result.edited.append(path)
    return contents


def _indexIdsCorrect(text: str) -> str:
    """Make each index row's Req ID the number of the record it links."""

    def fix(match: re.Match[str]) -> str:
        number = re.search(r"\]\(features/(\d{3})-", match.group(0))
        if not number:
            return match.group(0)
        return re.sub(
            r"^\|\s*[^|]*?\s*\|", f"| {number.group(1)} |", match.group(0), count=1
        )

    return re.sub(r"(?m)^\|[^\n]*\]\(features/[^\n]*$", fix, text)


def _linksRewrite(text: str, path: Path, moves: dict[Path, Path]) -> str:
    """Point relative links at renamed files, from the file's new location."""
    newParent = moves.get(path, path).parent

    def fix(match: re.Match[str]) -> str:
        target = match.group(2)
        if "://" in target or target.startswith(("#", "mailto:")):
            return match.group(0)
        linkPath, hashMark, anchor = target.partition("#")
        old = Path(os.path.normpath(path.parent / linkPath))
        if not old.exists() or (old not in moves and newParent == path.parent):
            return match.group(0)
        new = moves.get(old, old)
        relative = Path(os.path.relpath(new, newParent)).as_posix()
        return f"{match.group(1)}{relative}{hashMark}{anchor}{match.group(3)}"

    return _LINK_RE.sub(fix, text)


def _recordCorrect(text: str, path: Path, result: NamingCorrection) -> str:
    """Normalise the heading and Status section, and record the correction."""
    corrected = text
    heading = _HEADING_RE.match(corrected)
    if heading:
        wanted = f"# {heading.group(1)}: {heading.group(2).strip()}"
        corrected = corrected.replace(heading.group(0), wanted, 1)
    if not re.search(r"(?m)^## Status\s*$", corrected):
        corrected = re.sub(
            r"(?m)^Status:\s*([A-Za-z]+)\s*$", r"## Status\n\n\1", corrected, count=1
        )
    renamed = path in result.renames
    if corrected == text and not renamed:
        return text
    note = f"- {date.today().isoformat()}: {_NOTE_TEXT}" + (
        f" (was `{path.name}`)." if renamed else "."
    )
    if not re.search(r"(?mi)^## Change history\s*$", corrected):
        corrected = corrected.rstrip("\n") + "\n\n## Change history\n\n"
    if not corrected.endswith("\n\n"):
        corrected = corrected.rstrip("\n") + "\n"
    return corrected + note + "\n"


def _mentionsCollect(
    root: Path, result: NamingCorrection, contents: dict[Path, str]
) -> None:
    """List mentions of old names or prefixed IDs that correction leaves behind.

    The corrected text is scanned, so headings, index IDs and links this run
    fixes are not reported; files are reported at their corrected paths.
    """
    tokens = set()
    for source in result.renames:
        tokens.add(source.stem)
        prefixed = re.match(r"([A-Za-z]+-\d{3})-", source.name)
        if prefixed:
            tokens.add(prefixed.group(1))
    if not tokens:
        return
    pattern = re.compile(
        r"(?<![\w-])("
        + "|".join(re.escape(token) for token in sorted(tokens))
        + r")(?![\w])"
    )
    for path in _textFiles(root, _MENTION_SUFFIXES):
        try:
            text = contents.get(path) or path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        shown = result.renames.get(path, path)
        for number, lineText in enumerate(lines, start=1):
            # Link destinations are rewritten, and the correction's own
            # change-history note quotes the old name on purpose.
            if _NOTE_TEXT in lineText:
                continue
            unlinked = _LINK_RE.sub("", lineText)
            for found in pattern.findall(unlinked):
                result.mentions.append(
                    f"review mention of '{found}' at {_pathRelative(root, shown)}:{number}"
                )


## utilities


def _directoryRemoveEmpty(directory: Path, logger) -> None:
    try:
        directory.rmdir()
        _loggerAction(logger, f"removed empty legacy directory {directory}")
    except OSError:
        pass


def _fileMove(root: Path, source: Path, destination: Path) -> None:
    """Move with git when the file is tracked, so history follows it."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", str(source)],
        capture_output=True,
    )
    if tracked.returncode == 0:
        subprocess.run(
            ["git", "-C", str(root), "mv", str(source), str(destination)],
            check=True,
            capture_output=True,
        )
    else:
        source.rename(destination)


def _loggerAction(logger, message: str) -> None:
    if logger is not None:
        logger.action(message)


def _loggerInfo(logger, message: str) -> None:
    if logger is not None:
        logger.info(message)


def _pathRelative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _textFiles(root: Path, suffixes: tuple[str, ...]):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        if path.is_file() and path.suffix in suffixes and not pathGenerated(relative):
            yield path
