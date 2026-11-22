"""Resolve saved runtime choices and safely reconcile optional deployed copies."""

import ast
import os
import re
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from organiseMyProjects.runtimeDeployment import (
    runtimeDeploy,
    runtimeFiles,
    runtimeManaged,
    runtimeValidate,
)
from organiseMyProjects.wowAddon import isWowAddon

PREFERENCE_PATH = Path("project/project.yaml")
SCAN_SUFFIXES = {
    ".py",
    ".sh",
    ".bash",
    ".toml",
    ".cfg",
    ".ini",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".spec",
}
SCAN_EXCLUDED = {
    ".git",
    ".codex",
    ".agents",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "output",
    "build",
    "dist",
    "ompr",
}
_CHOICE_RE = re.compile(r"^localRuntime\s*:\s*(true|false)\s*(?:#.*)?$", re.IGNORECASE)
_REFERENCE_RE = re.compile(r"(?<![\w])ompr(?:[./\\]|\b)")


def preferenceContent(content: str, enabled: bool) -> str:
    """Update one validated scalar without reserialising project-owned metadata."""
    preferenceRead(content)
    lines = content.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if re.match(r"^localRuntime\s*:", line):
            # Keep inline comments and newline style with the user's other metadata.
            comment = " #" + line.split("#", 1)[1].rstrip("\r\n") if "#" in line else ""
            ending = "\r\n" if line.endswith("\r\n") else "\n"
            lines[index] = f"localRuntime: {str(enabled).lower()}{comment}{ending}"
            return "".join(lines)
    return (
        content
        + ("\n" if content and not content.endswith("\n") else "")
        + f"localRuntime: {str(enabled).lower()}\n"
    )


def preferenceRead(content: str) -> bool:
    """Read a strict top-level boolean; missing means disabled, never inferred."""
    found = []
    for line in content.splitlines():
        if re.search(
            r"[,{]\s*['\"]?localRuntime['\"]?\s*:", line
        ) and not line.lstrip().startswith("#"):
            raise ValueError(
                "localRuntime must be a top-level scalar, not a flow mapping"
            )
        if re.match(r"^\s*(?:['\"]?localRuntime['\"]?)\s*:", line):
            match = _CHOICE_RE.fullmatch(line)
            if match is None:
                raise ValueError(
                    "localRuntime must be an unquoted top-level true or false"
                )
            found.append(match.group(1).lower() == "true")
    if len(found) > 1:
        raise ValueError("duplicate localRuntime setting in project/project.yaml")
    return found[0] if found else False


def preferenceResolve(root: Path, requested: bool | None) -> tuple[bool, str]:
    """Validate saved configuration before applying an explicit override."""
    if requested is not None and not isinstance(requested, bool):
        raise ValueError("runtime choice must be true or false")
    path = root / PREFERENCE_PATH
    _pathValidate(root, path)
    content = path.read_bytes().decode("utf-8") if path.exists() else ""
    saved = preferenceRead(content)
    return (saved if requested is None else requested), content


def runtimeReconcile(
    root: Path, requested: bool | None, *, dryRun: bool, logger: Any
) -> bool:
    """Validate all runtime work before deployment, cleanup or preference writes."""
    root = Path(root)
    if root.resolve() == Path(__file__).resolve().parent.parent:
        raise ValueError(
            "canonical runtime sources must not receive a deployment preference"
        )
    if isWowAddon(root):
        if requested:
            raise ValueError("wow addons do not support --runtime")
        return False
    enabled, content = preferenceResolve(root, requested)
    logger.info(f"local runtime: {str(enabled).lower()}")
    removals = []
    if enabled:
        runtimeValidate(root)
    else:
        removals = runtimeRemovalPlan(root, logger)
    updated = preferenceContent(content, enabled)
    if updated != content:
        logger.action(
            f"{'would save' if dryRun else 'saving'} localRuntime: {str(enabled).lower()}"
        )
    if enabled:
        runtimeDeploy(root, dryRun=dryRun, logger=logger)
    elif removals:
        backup = root / "output" / "omprRuntimeBackups" / uuid4().hex
        _pathValidate(root, backup)
        logger.info(f"runtime recovery backup: {backup.relative_to(root)}")
        for path in removals:
            logger.action(
                f"{'would back up and remove' if dryRun else 'backing up and removing'} {path.relative_to(root)}"
            )
        if not dryRun:
            # Copy the entire removal set first: a failed backup never loses a helper.
            backup.mkdir(parents=True)
            for path in removals:
                destination = backup / path.relative_to(root / "ompr")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
            for path in removals:
                path.unlink()
            # Only discard empty parents of selected helpers, preserving links
            # and unrelated runtime content even when the manifest is extended.
            parents = {
                parent
                for path in removals
                for parent in path.parents
                if parent != root / "ompr" and (root / "ompr") in parent.parents
            }
            for parent in sorted(
                parents, key=lambda path: len(path.parts), reverse=True
            ):
                if not parent.is_symlink() and not any(parent.iterdir()):
                    parent.rmdir()
    target = root / "ompr"
    if (
        not enabled
        and not dryRun
        and target.is_dir()
        and not target.is_symlink()
        and not any(target.iterdir())
    ):
        target.rmdir()
    if not dryRun and updated != content:
        path = root / PREFERENCE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")
    return enabled


def runtimeRemovalPlan(root: Path, logger: Any) -> list[Path]:
    """Select only owned manifest files and reject unresolved consumer references."""
    target = root / "ompr"
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        logger.warning("preserving unowned or symlink runtime path: ompr")
        return []
    if not target.exists():
        return []
    init = target / "__init__.py"
    if any(target.iterdir()) and (
        init.is_symlink()
        or not init.is_file()
        or not runtimeManaged(init.read_text(encoding="utf-8"))
    ):
        logger.warning("preserving unowned ompr package; ownership requires review")
        return []
    removals = []
    for _source, relative in runtimeFiles():
        path = root / relative
        if (
            path.is_file()
            and not path.is_symlink()
            and runtimeManaged(path.read_text(encoding="utf-8"))
        ):
            removals.append(path)
    for path in target.iterdir():
        if path not in removals:
            logger.warning(
                f"preserving runtime content requiring review: {path.relative_to(root)}"
            )
    if removals:
        blockers = runtimeReferences(root)
        if blockers:
            raise ValueError(
                "runtime cleanup blocked; migrate imports, shell paths and packaging to installed organiseMyProjects first:\n"
                + "\n".join(blockers)
            )
    return removals


def runtimeReferences(root: Path) -> list[str]:
    """Find references across source and deployment files without following links."""
    blockers = []
    for directory, folders, files in os.walk(root, followlinks=False):
        for name in folders:
            path = Path(directory) / name
            if name not in SCAN_EXCLUDED and path.is_symlink():
                blockers.append(
                    f"{path.relative_to(root)}: symlink directory requires migration review"
                )
        folders[:] = [name for name in folders if name not in SCAN_EXCLUDED]
        for name in files:
            path = Path(directory) / name
            if path.suffix not in SCAN_SUFFIXES and name not in {
                "Dockerfile",
                "Makefile",
            }:
                continue
            relative = path.relative_to(root)
            if path.is_symlink():
                blockers.append(f"{relative}: symlink requires migration review")
                continue
            try:
                text = path.read_text(encoding="utf-8")
                if path.suffix == ".py":
                    # Ignore comments; include literal dynamic imports and shell commands.
                    tree = ast.parse(text)
                    referenced = any(
                        isinstance(node, ast.ImportFrom)
                        and node.level == 0
                        and (node.module or "").split(".")[0] == "ompr"
                        or isinstance(node, ast.Import)
                        and any(
                            alias.name.split(".")[0] == "ompr" for alias in node.names
                        )
                        or isinstance(node, ast.Constant)
                        and isinstance(node.value, str)
                        and _REFERENCE_RE.search(node.value)
                        for node in ast.walk(tree)
                    )
                else:
                    referenced = any(
                        _REFERENCE_RE.search(line)
                        for line in text.splitlines()
                        if not line.lstrip().startswith("#")
                    )
                if referenced:
                    blockers.append(f"{relative}: references ompr")
            except (OSError, UnicodeError, SyntaxError) as exc:
                blockers.append(f"{relative}: cannot verify runtime references ({exc})")
    return blockers


def _pathValidate(root: Path, path: Path) -> None:
    """Refuse links in configuration and backup destinations before any mutation."""
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError(
                f"runtime configuration/backup path is a symlink: {current}"
            )
        if current.exists() and current != path and not current.is_dir():
            raise ValueError(
                f"runtime configuration/backup parent is not a directory: {current}"
            )
        current = current.parent
