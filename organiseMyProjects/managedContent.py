"""Release-marker and managed-block helpers for OMP-owned files."""

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


def managedBlockRender(inner: str, commentPrefix: str) -> str:
    """Return a managed block including begin and end markers."""
    innerText = inner.rstrip("\n")
    return (
        f"{commentPrefix} {MANAGED_BLOCK_BEGIN}\n"
        f"{innerText}\n"
        f"{commentPrefix} {MANAGED_BLOCK_END}\n"
    )


def managedBlockMergeText(
    existing: str, blockInner: str, commentPrefix: str, *, jsonStyle: bool = False
) -> str:
    """Replace or insert a managed block in existing file text."""
    block = managedBlockRender(blockInner, commentPrefix)
    beginLine = f"{commentPrefix} {MANAGED_BLOCK_BEGIN}"
    endLine = f"{commentPrefix} {MANAGED_BLOCK_END}"
    beginIndex = existing.find(beginLine)
    endIndex = existing.find(endLine)
    if beginIndex != -1 and endIndex != -1 and endIndex > beginIndex:
        newlineIndex = existing.find("\n", endIndex)
        if newlineIndex == -1:
            endIndex = len(existing)
        else:
            endIndex = newlineIndex + 1
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
