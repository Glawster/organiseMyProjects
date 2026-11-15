"""Select and safely deploy the self-contained OMPR runtime subset."""

import ast
from pathlib import Path
from typing import Any

from organiseMyProjects.managedContent import managedContentBody, managedContentBuild

# An explicit allowlist prevents tooling, UI and application code from leaking
# into consumers. Adding a self-contained helper here extends every deployment.
RUNTIME_FILES = (
    ("runtimeInit.py", "__init__.py"),
    ("logUtils.py", "logUtils.py"),
    ("logUtils.sh", "logUtils.sh"),
    ("version.py", "version.py"),
)


def runtimeDeploy(root: Path, *, dryRun: bool, logger: Any) -> None:
    """Refresh managed helpers, preserving unchanged content and file modes."""
    runtimeValidate(root)
    # Validate the entire destination before making the first runtime change.
    for source, relative in runtimeFiles():
        destination = root / relative
        body = source.read_text(encoding="utf-8")
        content = managedContentBuild(body, suffix=destination.suffix)
        previous = (
            destination.read_text(encoding="utf-8") if destination.exists() else ""
        )
        oldBody, markers = managedContentBody(previous)
        newBody, _ = managedContentBody(content)
        changed = markers != 1 or oldBody != newBody
        sourceMode = source.stat().st_mode & 0o111
        modeChanged = (
            destination.exists() and destination.stat().st_mode & 0o111 != sourceMode
        )
        if not changed and not modeChanged:
            continue
        logger.action(f"{'would deploy' if dryRun else 'deploying'} runtime {relative}")
        if dryRun:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if changed:
            destination.write_text(content, encoding="utf-8")
        destination.chmod((destination.stat().st_mode & ~0o111) | sourceMode)


def runtimeFiles() -> list[tuple[Path, Path]]:
    """Return canonical source paths and their consumer-relative destinations."""
    return [
        (Path(__file__).parent / source, Path("ompr") / target)
        for source, target in RUNTIME_FILES
    ]


def runtimeMigrationReport(root: Path, logger: Any) -> None:
    """Report legacy imports and packaging review without editing application code."""
    # Scan application roots only, avoiding environments, caches and vendored
    # dependencies. Existing packaging remains project-owned on ordinary update.
    candidates = list(root.glob("*.py"))
    for name in (root.name, "src", "scripts"):
        folder = root / name
        if folder.is_dir() and not folder.is_symlink():
            candidates.extend(folder.rglob("*.py"))
    for path in sorted(set(candidates)):
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            logger.warning(
                f"runtime migration could not inspect {path.relative_to(root)}"
            )
            continue
        if any(
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and (node.module or "").split(".")[0] == "organiseMyProjects"
            or isinstance(node, ast.Import)
            and any(
                alias.name.split(".")[0] == "organiseMyProjects" for alias in node.names
            )
            for node in ast.walk(tree)
        ):
            logger.warning(
                f"runtime migration review: {path.relative_to(root)} imports organiseMyProjects; "
                "use ompr for deployed runtime helpers; retain tooling imports only for development"
            )
    logger.warning(
        "runtime packaging review: include ompr and its shell helper in the application "
        "distribution; remove ompr tooling from runtime dependencies only after "
        "migrating imports and verifying an isolated installation"
    )


def runtimeValidate(root: Path) -> None:
    """Refuse symlink escapes and collisions with project-owned runtime files."""
    if root.resolve() == Path(__file__).resolve().parent.parent:
        raise ValueError("canonical runtime sources must not receive a deployment copy")
    target = root / "ompr"
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError(f"runtime destination is not a regular directory: {target}")
    if target.exists() and any(target.iterdir()):
        init = target / "__init__.py"
        if init.is_symlink() or not init.is_file():
            raise ValueError(f"project-owned ompr directory requires review: {target}")
        if not managedContentBody(init.read_text(encoding="utf-8"))[1]:
            raise ValueError(f"project-owned ompr package requires review: {target}")
    for source, relative in runtimeFiles():
        if not source.is_file():
            raise ValueError(f"runtime source is unavailable: {source}")
        path = root / relative
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"runtime destination requires review: {path}")
        if not path.resolve().is_relative_to(target.resolve()):
            raise ValueError(f"runtime destination escapes managed package: {path}")
        if (
            path.exists()
            and not managedContentBody(path.read_text(encoding="utf-8"))[1]
        ):
            raise ValueError(f"project-owned runtime file requires review: {path}")
