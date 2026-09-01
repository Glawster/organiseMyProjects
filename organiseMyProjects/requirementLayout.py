"""OMP 0.6 requirement, prompt, and folder-index layout compatibility.

The migration is intentionally conservative. It recognises only known OMP
index shapes and deterministic per-requirement/per-prompt directory forms.
Arbitrary user-owned README files and multi-file directories are preserved.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

_INDEX_MIGRATIONS = (
    (
        Path("project/requirements/README.md"),
        Path("project/requirements/folderIndex.md"),
        ("# Requirements", "Next available number:", "## Requirement index"),
    ),
    (
        Path("project/requirements/requirementsIndex.md"),
        Path("project/requirements/folderIndex.md"),
        ("# Requirements", "Next available number:", "## Requirement index"),
    ),
    (
        Path("project/adr/README.md"),
        Path("project/adr/folderIndex.md"),
        (
            "# Architecture Decision Records",
            "Next available number:",
            "## Decision index",
        ),
    ),
    (
        Path("project/adr/adrIndex.md"),
        Path("project/adr/folderIndex.md"),
        (
            "# Architecture Decision Records",
            "Next available number:",
            "## Decision index",
        ),
    ),
)

_REFERENCE_REPLACEMENTS = (
    ("project/requirements/README.md", "project/requirements/folderIndex.md"),
    (
        "project/requirements/requirementsIndex.md",
        "project/requirements/folderIndex.md",
    ),
    ("project/adr/README.md", "project/adr/folderIndex.md"),
    ("project/adr/adrIndex.md", "project/adr/folderIndex.md"),
    ("requirements/README.md", "requirements/folderIndex.md"),
    ("requirements/requirementsIndex.md", "requirements/folderIndex.md"),
    ("adr/README.md", "adr/folderIndex.md"),
    ("adr/adrIndex.md", "adr/folderIndex.md"),
)

_REQUIREMENT_DIR_RE = re.compile(r"^(\d{3})-([A-Za-z][A-Za-z0-9_-]*)$")
_PROMPT_DIR_RE = re.compile(r"^(\d{3}[a-z]?)-([A-Za-z][A-Za-z0-9_-]*)$")


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
    return text is not None and all(marker in text for marker in markers)


def _referencePathsIterate(basePath: Path):
    for path in basePath.rglob("*.md"):
        if ".git" in path.parts:
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
            _loggerAction(logger, f"would update folder-index reference {path}")
        else:
            path.write_text(updated, encoding="utf-8")
            _loggerAction(logger, f"updated folder-index reference {path}")


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
            # A freshly scaffolded empty legacy index can be discarded when a
            # real folderIndex already owns the directory state.
            scaffoldOnly = "Next available number: 001" in (
                oldText or ""
            ) and not re.search(r"^\|\s*\d{3}\s*\|", oldText or "", re.MULTILINE)
            if not scaffoldOnly:
                _loggerInfo(
                    logger,
                    f"folder index migration skipped because target exists: {newPath}",
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


def manageProjectPatchesInstall(manageProjectModule) -> None:
    """Wrap project-management entry points with requirement 004 migration."""
    if getattr(manageProjectModule, "_requirement004Patched", False):
        return

    originalCreate: Callable = manageProjectModule.createProject
    originalMigrate: Callable = manageProjectModule.migrateProject
    originalUpdate: Callable = manageProjectModule.updateProject

    def createProject(*args, **kwargs):
        result = originalCreate(*args, **kwargs)
        projectPath = _projectPathResolve(args, kwargs)
        if projectPath is not None:
            layoutMigrate(
                projectPath,
                dryRun=_dryRunResolve(args, kwargs),
                logger=manageProjectModule.logger,
            )
        return result

    def migrateProject(*args, **kwargs):
        result = originalMigrate(*args, **kwargs)
        projectPath = _projectPathResolve(args, kwargs)
        if projectPath is not None:
            layoutMigrate(
                projectPath,
                dryRun=_dryRunResolve(args, kwargs),
                logger=manageProjectModule.logger,
            )
        return result

    def updateProject(*args, **kwargs):
        result = originalUpdate(*args, **kwargs)
        projectPath = _projectPathResolve(args, kwargs)
        if projectPath is not None:
            layoutMigrate(
                projectPath,
                dryRun=_dryRunResolve(args, kwargs),
                logger=manageProjectModule.logger,
            )
        return result

    manageProjectModule.createProject = createProject
    manageProjectModule.migrateProject = migrateProject
    manageProjectModule.updateProject = updateProject
    manageProjectModule._requirement004Patched = True


def agentCheckPatchesInstall(agentCheckModule) -> None:
    """Teach agent readiness checks about folderIndex.md and nested README policy."""
    validator = agentCheckModule.AgentCheckValidator
    if getattr(validator, "_requirement004Patched", False):
        return

    originalDocumentation = validator._checkDocumentation
    originalRequirements = validator._checkRequirementsAndAdrs

    def _checkDocumentation(self):
        originalDocumentation(self)
        for readme in self.rootPath.rglob("README.md"):
            if readme == self.rootPath / "README.md" or ".git" in readme.parts:
                continue
            self.report.add(
                "DOC-005",
                agentCheckModule.Severity.FAILURE,
                "README.md is reserved for the repository root; use folderIndex.md for directory indexes",
                readme,
            )

    def _checkRequirementsAndAdrs(self):
        reqDir = self.rootPath / "project" / "requirements"
        indexPath = reqDir / "folderIndex.md"
        legacyPaths = (reqDir / "README.md", reqDir / "requirementsIndex.md")
        existingLegacy = next((path for path in legacyPaths if path.exists()), None)
        if existingLegacy is not None:
            # DOC-005 reports README specifically; legacy named indexes remain
            # migration targets. Run the old validation only for README shape.
            if existingLegacy.name == "README.md":
                originalRequirements(self)
            return
        if not indexPath.exists():
            return

        featuresDir = reqDir / "features"
        if not featuresDir.is_dir():
            return
        featureFiles = {path.name: path for path in featuresDir.glob("*.md")}
        promptsDir = reqDir / "prompt"
        try:
            indexText = indexPath.read_text(encoding="utf-8")
        except OSError:
            return

        for featureName, featurePath in featureFiles.items():
            if featureName not in indexText:
                self.report.add(
                    "REQ-001",
                    agentCheckModule.Severity.FAILURE,
                    f"Requirement '{featureName}' is not listed in project/requirements/folderIndex.md index",
                    featurePath,
                )
            try:
                featureText = featurePath.read_text(encoding="utf-8")
            except OSError:
                continue
            statusMatch = re.search(r"## Status\s*\n+([A-Za-z]+)", featureText)
            featureStatus = statusMatch.group(1).strip() if statusMatch else ""
            rowMatch = re.search(
                rf"\|\s*\d+\s*\|\s*\[.*?\]\(features/{re.escape(featureName)}\)\s*\|\s*.*?\s*\|\s*([A-Za-z]+)\s*\|",
                indexText,
            )
            if (
                rowMatch
                and featureStatus.casefold() != rowMatch.group(1).strip().casefold()
            ):
                self.report.add(
                    "REQ-002",
                    agentCheckModule.Severity.FAILURE,
                    f"Status mismatch for {featureName}: folderIndex index states '{rowMatch.group(1).strip()}' but record states '{featureStatus}'",
                    featurePath,
                )

        promptLinks = re.findall(r"\]\(prompt/([^)]+\.md)\)", indexText)
        for promptName in promptLinks:
            if ".prompt.md" in promptName:
                self.report.add(
                    "REQ-005",
                    agentCheckModule.Severity.FAILURE,
                    f"Prompt '{promptName}' uses the obsolete .prompt infix",
                    indexPath,
                )
            baseName = re.sub(r"^(\d{3})[a-z]-", r"\1-", promptName)
            if baseName not in featureFiles:
                self.report.add(
                    "REQ-005",
                    agentCheckModule.Severity.FAILURE,
                    f"Prompt '{promptName}' has no deterministic requirement filename match",
                    indexPath,
                )
            if promptsDir.is_dir() and not (promptsDir / promptName).exists():
                self.report.add(
                    "REQ-005",
                    agentCheckModule.Severity.FAILURE,
                    f"Prompt '{promptName}' linked from the index does not exist",
                    indexPath,
                )

        adrDir = self.rootPath / "project" / "adr"
        if adrDir.is_dir():
            for featurePath in featureFiles.values():
                try:
                    featureText = featurePath.read_text(encoding="utf-8")
                except OSError:
                    continue
                for adrName in re.findall(
                    r"project/adr/(\d{3}-[A-Za-z0-9_-]+\.md)", featureText
                ):
                    if not (adrDir / adrName).exists():
                        self.report.add(
                            "REQ-003",
                            agentCheckModule.Severity.FAILURE,
                            f"Requirement '{featurePath.name}' references non-existent ADR 'project/adr/{adrName}'",
                            featurePath,
                        )

    validator._checkDocumentation = _checkDocumentation
    validator._checkRequirementsAndAdrs = _checkRequirementsAndAdrs
    validator._requirement004Patched = True
