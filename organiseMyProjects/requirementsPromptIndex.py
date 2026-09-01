"""Maintain prompt navigation in the requirements index."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

_PROMPT_FILE_RE = re.compile(r"^\d{3}[a-z]?-[A-Za-z][A-Za-z0-9_-]*\.md$")
_PROMPT_INDEX_BEGIN = "<!-- OMP-PROMPT-INDEX-BEGIN -->"
_PROMPT_INDEX_END = "<!-- OMP-PROMPT-INDEX-END -->"


def _loggerAction(logger, message: str) -> None:
    if logger is not None:
        logger.action(message)


def _promptFiles(root: Path) -> list[Path]:
    promptDir = root / "project" / "requirements" / "prompt"
    if not promptDir.is_dir():
        return []
    return sorted(
        path
        for path in promptDir.glob("*.md")
        if _PROMPT_FILE_RE.fullmatch(path.name) is not None
    )


def _promptIndexBlock(promptFiles: list[Path]) -> str:
    lines = ["## Prompt index", "", _PROMPT_INDEX_BEGIN]
    if promptFiles:
        lines.extend(f"- [{path.stem}](prompt/{path.name})" for path in promptFiles)
    else:
        lines.append("None.")
    lines.extend([_PROMPT_INDEX_END, ""])
    return "\n".join(lines)


def promptIndexEnsure(
    basePath: Path | str,
    dryRun: bool = False,
    logger=None,
) -> None:
    """Ensure requirementsIndex.md lists every flat requirement prompt."""
    root = Path(basePath)
    indexPath = root / "project" / "requirements" / "requirementsIndex.md"
    if not indexPath.is_file():
        return

    try:
        existing = indexPath.read_text(encoding="utf-8")
    except OSError:
        return

    promptFiles = _promptFiles(root)
    block = _promptIndexBlock(promptFiles)
    beginIndex = existing.find(_PROMPT_INDEX_BEGIN)
    endIndex = existing.find(_PROMPT_INDEX_END)

    if beginIndex != -1 and endIndex != -1 and endIndex > beginIndex:
        headingIndex = existing.rfind("## Prompt index", 0, beginIndex)
        replaceStart = headingIndex if headingIndex != -1 else beginIndex
        replaceEnd = endIndex + len(_PROMPT_INDEX_END)
        while replaceEnd < len(existing) and existing[replaceEnd] == "\n":
            replaceEnd += 1
        updated = existing[:replaceStart].rstrip() + "\n\n" + block + existing[replaceEnd:]
    elif "## Prompt index" in existing:
        # Preserve an existing project-owned prompt index rather than replacing it.
        return
    else:
        updated = existing.rstrip() + "\n\n" + block

    if updated == existing:
        return
    if dryRun:
        _loggerAction(logger, f"would update prompt index {indexPath}")
        return

    indexPath.write_text(updated, encoding="utf-8")
    _loggerAction(logger, f"updated prompt index {indexPath}")


def _projectPathResolve(args, kwargs) -> Path | str | None:
    if args:
        return args[0]
    return kwargs.get("projectName")


def _dryRunResolve(args, kwargs) -> bool:
    if "dryRun" in kwargs:
        return bool(kwargs["dryRun"])
    if len(args) > 1:
        return bool(args[1])
    return False


def promptIndexPatchesInstall(manageProjectModule, agentCheckModule) -> None:
    """Install prompt-index maintenance on manageProject and agentCheck."""
    if getattr(manageProjectModule, "_requirementsPromptIndexPatched", False):
        return

    for functionName in ("createProject", "migrateProject", "updateProject"):
        original: Callable = getattr(manageProjectModule, functionName)

        def wrapped(*args, _original=original, **kwargs):
            result = _original(*args, **kwargs)
            projectPath = _projectPathResolve(args, kwargs)
            if projectPath is not None:
                promptIndexEnsure(
                    projectPath,
                    dryRun=_dryRunResolve(args, kwargs),
                    logger=manageProjectModule.logger,
                )
            return result

        setattr(manageProjectModule, functionName, wrapped)

    validator = agentCheckModule.AgentCheckValidator
    originalRequirements = validator._checkRequirementsAndAdrs

    def _checkRequirementsAndAdrs(self):
        originalRequirements(self)
        root = self.rootPath
        indexPath = root / "project" / "requirements" / "requirementsIndex.md"
        if not indexPath.is_file():
            return
        try:
            indexText = indexPath.read_text(encoding="utf-8")
        except OSError:
            return

        for promptPath in _promptFiles(root):
            expected = f"prompt/{promptPath.name}"
            if expected not in indexText:
                self.report.add(
                    "REQ-006",
                    agentCheckModule.Severity.FAILURE,
                    f"Requirement prompt '{promptPath.name}' is not listed in requirementsIndex.md",
                    promptPath,
                )

    validator._checkRequirementsAndAdrs = _checkRequirementsAndAdrs
    manageProjectModule._requirementsPromptIndexPatched = True
