"""Release-marker and managed-block helpers for OMP-owned files."""

import re
from pathlib import Path

from organiseMyProjects.version import VERSION

DEPLOYMENT_COMMENT = (
    f"<!-- deployed from Glawster/organiseMyProjects release {VERSION} "
    "-- do not edit directly -->\n"
)
PYTHON_DEPLOYMENT_COMMENT = (
    f"# deployed from Glawster/organiseMyProjects release {VERSION} "
    "-- do not edit directly\n"
)
SYNC_COMMENT = (
    f"<!-- synced from Glawster/organiseMyProjects release {VERSION} "
    "-- do not edit directly -->\n"
)
PYTHON_SYNC_COMMENT = (
    f"# synced from Glawster/organiseMyProjects release {VERSION} "
    "-- do not edit directly\n"
)

MARKER_PREFIXES = (
    "<!-- deployed from Glawster/organiseMyProjects release ",
    "<!-- synced from Glawster/organiseMyProjects release ",
    "# deployed from Glawster/organiseMyProjects release ",
    "# synced from Glawster/organiseMyProjects release ",
)

MANAGED_BLOCK_BEGIN = "OMP-MANAGED-BEGIN"
MANAGED_BLOCK_END = "OMP-MANAGED-END"

POLICY_MANAGED_OVERWRITE = "managed-overwrite"
POLICY_MANAGED_BLOCK_MERGE = "managed-block-merge"
POLICY_PROJECT_OWNED_MISSING_ONLY = "project-owned-missing-only"

_PYTHON_LIKE_SUFFIXES = {".py", ".sh"}
_ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*=")
_JSON_PROPERTY_RE = re.compile(r'^\s*"([^"]+)"\s*:')
_HOOK_ID_RE = re.compile(r"(?m)^\s*- id:\s*(\S+)\s*$")
_YAML_ITEM_START_RE = re.compile(r"^(\s*)- ")
_YAML_PACKAGE_RE = re.compile(r"^\s*-\s+([A-Za-z0-9_.-]+)(?:\s*$|[<>=!~[])")
_REQUIREMENT_NAME_RE = re.compile(r"^([A-Za-z0-9_.-]+)")


def managedContentBody(content: str) -> tuple[str, int]:
    """Return content without leading OMP release markers and their count."""
    lines = content.splitlines(keepends=True)
    if not lines:
        return content, 0

    markerIndex = 1 if lines[0].startswith("#!") else 0
    markerCount = 0
    while markerIndex < len(lines) and lines[markerIndex].startswith(MARKER_PREFIXES):
        del lines[markerIndex]
        markerCount += 1

    return "".join(lines), markerCount


def managedContentBuild(
    sourceContent: str,
    suffix: str = ".md",
    *,
    sync: bool = False,
) -> str:
    """Add the scaffold release marker to canonical managed content."""
    sourceContent, _ = managedContentBody(sourceContent)
    marker = PYTHON_SYNC_COMMENT if sync else PYTHON_DEPLOYMENT_COMMENT
    markdownMarker = SYNC_COMMENT if sync else DEPLOYMENT_COMMENT
    if suffix not in _PYTHON_LIKE_SUFFIXES:
        return markdownMarker + sourceContent

    if sourceContent.startswith("#!"):
        shebang, separator, remainder = sourceContent.partition("\n")
        return shebang + separator + marker + remainder
    return marker + sourceContent


def commentPrefixFor(path: Path) -> str:
    """Return the line-comment prefix used for managed blocks in ``path``."""
    if path.suffix == ".json":
        return "//"
    return "#"


def _contentIndent(text: str) -> str:
    """Return leading whitespace from the first non-empty line."""
    for line in text.splitlines():
        if line.strip():
            return line[: len(line) - len(line.lstrip())]
    return ""


def managedBlockRender(inner: str, commentPrefix: str) -> str:
    """Return a managed block including begin and end markers."""
    innerText = inner.rstrip("\n")
    indent = _contentIndent(innerText)
    return (
        f"{indent}{commentPrefix} {MANAGED_BLOCK_BEGIN}\n"
        f"{innerText}\n"
        f"{indent}{commentPrefix} {MANAGED_BLOCK_END}\n"
    )


def _managedAssignmentDuplicatesRemove(
    existing: str,
    blockInner: str,
    beginLine: str,
    endLine: str,
) -> str:
    """Remove unmanaged scalar assignments now owned by the managed block."""
    managedKeys = {
        match.group(1)
        for line in blockInner.splitlines()
        if (match := _ASSIGNMENT_RE.match(line)) is not None
    }
    if not managedKeys:
        return existing

    kept = []
    insideManagedBlock = False
    for line in existing.splitlines(keepends=True):
        stripped = line.strip()
        if stripped == beginLine:
            insideManagedBlock = True
            kept.append(line)
            continue
        if stripped == endLine:
            insideManagedBlock = False
            kept.append(line)
            continue

        match = _ASSIGNMENT_RE.match(line)
        if (
            not insideManagedBlock
            and match is not None
            and match.group(1) in managedKeys
        ):
            continue
        kept.append(line)

    return "".join(kept)


def _managedJsonDuplicatesRemove(
    existing: str,
    blockInner: str,
    beginLine: str,
    endLine: str,
) -> str:
    """Remove unmanaged JSON properties now owned by the managed block."""
    managedKeys = {
        match.group(1)
        for line in blockInner.splitlines()
        if (match := _JSON_PROPERTY_RE.match(line)) is not None
    }
    if not managedKeys:
        return existing

    kept = []
    insideManagedBlock = False
    skippingProperty = False
    propertyIndent = 0

    for line in existing.splitlines(keepends=True):
        stripped = line.strip()
        if stripped == beginLine:
            insideManagedBlock = True
            skippingProperty = False
            kept.append(line)
            continue
        if stripped == endLine:
            insideManagedBlock = False
            kept.append(line)
            continue

        match = _JSON_PROPERTY_RE.match(line)
        indent = len(line) - len(line.lstrip())

        if skippingProperty:
            if match is not None and indent <= propertyIndent:
                skippingProperty = False
            elif stripped == "}" and indent <= propertyIndent:
                skippingProperty = False
            else:
                continue

        if (
            not insideManagedBlock
            and match is not None
            and match.group(1) in managedKeys
        ):
            propertyIndent = indent
            skippingProperty = True
            continue

        kept.append(line)

    return "".join(kept)


def _requirementName(line: str) -> str | None:
    """Return the distribution name from a requirements line, if any."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("-"):
        return None
    if re.match(r"^[A-Za-z_][A-Za-z0-9_.-]*\s+=", stripped):
        return None
    if re.match(r"^[A-Za-z0-9_.-]+\s*:", stripped):
        return None
    match = _REQUIREMENT_NAME_RE.match(stripped)
    if match is None:
        return None
    return match.group(1).lower()


def _managedRequirementDuplicatesRemove(
    existing: str,
    blockInner: str,
    beginLine: str,
    endLine: str,
) -> str:
    """Remove unmanaged requirement lines now owned by the managed block."""
    managedNames = {
        name
        for line in blockInner.splitlines()
        if (name := _requirementName(line)) is not None
    }
    if not managedNames:
        return existing

    kept = []
    insideManagedBlock = False
    for line in existing.splitlines(keepends=True):
        stripped = line.strip()
        if stripped == beginLine:
            insideManagedBlock = True
            kept.append(line)
            continue
        if stripped == endLine:
            insideManagedBlock = False
            kept.append(line)
            continue
        name = _requirementName(line)
        if not insideManagedBlock and name is not None and name in managedNames:
            continue
        kept.append(line)
    return "".join(kept)


def _yamlItemEndIndex(lines: list[str], start: int, indent: int) -> int:
    """Return the exclusive end index of a YAML sequence item."""
    index = start + 1
    while index < len(lines):
        raw = lines[index]
        if raw.strip() == "":
            index += 1
            continue
        currentIndent = len(raw) - len(raw.lstrip())
        if currentIndent <= indent:
            break
        index += 1
    return index


def _managedYamlDuplicatesRemove(
    existing: str,
    blockInner: str,
    beginLine: str,
    endLine: str,
) -> str:
    """Remove unmanaged YAML items now owned by the managed block."""
    managedHookIds = {match.group(1) for match in _HOOK_ID_RE.finditer(blockInner)}
    managedPackages = {
        match.group(1).lower()
        for line in blockInner.splitlines()
        if (match := _YAML_PACKAGE_RE.match(line)) is not None
    }
    if not managedHookIds and not managedPackages:
        return existing

    managedIndent = None
    for managedLine in blockInner.splitlines():
        startMatch = _YAML_ITEM_START_RE.match(managedLine)
        if startMatch is not None:
            managedIndent = len(startMatch.group(1))
            break

    lines = existing.splitlines(keepends=True)
    kept: list[str] = []
    insideManagedBlock = False
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped == beginLine:
            insideManagedBlock = True
            kept.append(line)
            index += 1
            continue
        if stripped == endLine:
            insideManagedBlock = False
            kept.append(line)
            index += 1
            continue

        startMatch = _YAML_ITEM_START_RE.match(line)
        if (
            startMatch is not None
            and not insideManagedBlock
            and (managedIndent is None or len(startMatch.group(1)) == managedIndent)
        ):
            indent = len(startMatch.group(1))
            end = _yamlItemEndIndex(lines, index, indent)
            itemText = "".join(lines[index:end])
            hookIds = {match.group(1) for match in _HOOK_ID_RE.finditer(itemText)}
            packageMatch = _YAML_PACKAGE_RE.match(line)
            packageName = (
                packageMatch.group(1).lower() if packageMatch is not None else None
            )
            if hookIds & managedHookIds or (
                packageName is not None and packageName in managedPackages
            ):
                index = end
                continue
        kept.append(line)
        index += 1
    return "".join(kept)


def managedBlockMergeText(
    existing: str, blockInner: str, commentPrefix: str, *, jsonStyle: bool = False
) -> str:
    """Replace or insert a managed block and adopt matching settings."""
    block = managedBlockRender(blockInner, commentPrefix)
    beginLine = f"{commentPrefix} {MANAGED_BLOCK_BEGIN}"
    endLine = f"{commentPrefix} {MANAGED_BLOCK_END}"
    if jsonStyle:
        existing = _managedJsonDuplicatesRemove(
            existing,
            blockInner,
            beginLine,
            endLine,
        )
    else:
        existing = _managedAssignmentDuplicatesRemove(
            existing,
            blockInner,
            beginLine,
            endLine,
        )
        existing = _managedRequirementDuplicatesRemove(
            existing,
            blockInner,
            beginLine,
            endLine,
        )
        existing = _managedYamlDuplicatesRemove(
            existing,
            blockInner,
            beginLine,
            endLine,
        )
    lines = existing.splitlines(keepends=True)
    beginIndex = None
    endIndex = None
    offset = 0
    for line in lines:
        stripped = line.strip()
        if beginIndex is None and stripped == beginLine:
            beginIndex = offset
        if stripped == endLine:
            endIndex = offset + len(line)
        offset += len(line)
    if beginIndex is not None and endIndex is not None and endIndex > beginIndex:
        return existing[:beginIndex] + block + existing[endIndex:]

    if jsonStyle:
        return _jsonInsertManagedBlock(existing, block)
    text = existing
    if text and not text.endswith("\n"):
        text += "\n"
    if text:
        text += "\n"
    return text + block


def _jsonInsertManagedBlock(existing: str, block: str) -> str:
    """Insert a comment-delimited managed block before the last closing brace."""
    stripped = existing.rstrip()
    if not stripped.endswith("}"):
        text = existing
        if text and not text.endswith("\n"):
            text += "\n"
        return text + "\n" + block

    head = stripped[:-1].rstrip()
    if head.endswith("{"):
        return head + "\n" + block + "}\n"
    if not head.endswith(","):
        head += ","
    return head + "\n" + block + "}\n"
