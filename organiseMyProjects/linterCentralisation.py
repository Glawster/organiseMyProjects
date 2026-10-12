"""OMP 0.8 migration from copied project linters to the installed package."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

OBSOLETE_LINTER_PATHS = (
    Path("tests/runLinter.py"),
    Path("tests/guiNamingLinter.py"),
)
LINTER_GUIDE_PATH = Path("documentation/linter.md")


def _canonicalSource(manageProjectModule, relative: Path) -> Path:
    return manageProjectModule.TEMPLATE_DIR / relative.name


def _managedBody(manageProjectModule, text: str) -> tuple[str, int]:
    return manageProjectModule._managedContentBody(text)


def _obsoleteCopyRecognised(manageProjectModule, path: Path, relative: Path) -> bool:
    """Recognise only unmodified current or explicitly managed linter copies."""
    try:
        deployed = path.read_text(encoding="utf-8")
        canonical = _canonicalSource(manageProjectModule, relative).read_text(
            encoding="utf-8"
        )
    except OSError:
        return False

    deployedBody, markerCount = _managedBody(manageProjectModule, deployed)
    canonicalBody, _ = _managedBody(manageProjectModule, canonical)
    if markerCount:
        return deployedBody == canonicalBody
    return deployed == canonical


def obsoleteLinterCopiesRemove(
    manageProjectModule,
    basePath: Path | str,
    dryRun: bool = False,
) -> None:
    """Remove recognised old copies and preserve ambiguous/local variants."""
    root = Path(basePath)
    for relative in OBSOLETE_LINTER_PATHS:
        path = root / relative
        if not path.is_file():
            continue
        if not _obsoleteCopyRecognised(manageProjectModule, path, relative):
            manageProjectModule.logger.info(
                f"obsolete linter preserved because ownership or local changes are ambiguous: {path}"
            )
            continue
        if dryRun:
            manageProjectModule.logger.action(
                f"would remove obsolete managed linter {path}"
            )
            continue
        path.unlink()
        manageProjectModule.logger.action(f"removed obsolete managed linter {path}")


def _managedTemplatesFilter(manageProjectModule) -> None:
    obsolete = {path.as_posix() for path in OBSOLETE_LINTER_PATHS}
    manageProjectModule.MANAGED_COPY_TEMPLATES[:] = [
        (source, destination)
        for source, destination in manageProjectModule.MANAGED_COPY_TEMPLATES
        if destination.as_posix() not in obsolete
    ]

    guideSource = manageProjectModule.TEMPLATE_DIR.parent / LINTER_GUIDE_PATH
    if guideSource.exists() and not any(
        destination == LINTER_GUIDE_PATH
        for _source, destination in manageProjectModule.MANAGED_COPY_TEMPLATES
    ):
        manageProjectModule.MANAGED_COPY_TEMPLATES.append(
            (guideSource, LINTER_GUIDE_PATH)
        )
        manageProjectModule.FILE_OWNERSHIP[LINTER_GUIDE_PATH.as_posix()] = (
            manageProjectModule.POLICY_MANAGED_OVERWRITE
        )


def manageProjectLinterPatchesInstall(manageProjectModule) -> None:
    """Make package linters authoritative for create and update operations."""
    if getattr(manageProjectModule, "_requirement008LinterPatched", False):
        return

    _managedTemplatesFilter(manageProjectModule)

    originalModulesIterate: Callable = manageProjectModule._templateModulesIterate

    def _templateModulesIterate(*args, **kwargs):
        obsolete = {path.as_posix() for path in OBSOLETE_LINTER_PATHS}
        return [
            (source, destination)
            for source, destination in originalModulesIterate(*args, **kwargs)
            if destination.as_posix() not in obsolete
        ]

    manageProjectModule._templateModulesIterate = _templateModulesIterate

    originalCreate: Callable = manageProjectModule.createProject
    originalUpdate: Callable = manageProjectModule.updateProject

    def createProject(*args, **kwargs):
        result = originalCreate(*args, **kwargs)
        projectPath = args[0] if args else kwargs.get("projectName")
        dryRun = bool(kwargs.get("dryRun", args[1] if len(args) > 1 else False))
        if projectPath is None:
            return result
        guideSource = manageProjectModule.TEMPLATE_DIR.parent / LINTER_GUIDE_PATH
        root = Path(projectPath)
        if root.exists() and guideSource.exists():
            manageProjectModule._managedCopyUpdate(
                guideSource, root / LINTER_GUIDE_PATH, dryRun
            )
        return result

    def updateProject(*args, **kwargs):
        projectPath = args[0] if args else kwargs.get("projectName")
        dryRun = bool(kwargs.get("dryRun", args[1] if len(args) > 1 else False))
        if projectPath is not None:
            obsoleteLinterCopiesRemove(
                manageProjectModule,
                projectPath,
                dryRun=dryRun,
            )
        return originalUpdate(*args, **kwargs)

    manageProjectModule.createProject = createProject
    manageProjectModule.updateProject = updateProject
    manageProjectModule._requirement008LinterPatched = True
