import os
import shutil
import subprocess
import argparse
import importlib.util
import sys
from pathlib import Path

from organiseMyProjects.logUtils import getLogger, setApplication
from organiseMyProjects.version import VERSION

thisApplication = Path(__file__).stem
setApplication(thisApplication)
logger = getLogger(includeConsole=False)

DEPLOYMENT_COMMENT = (
    f"<!-- deployed from Glawster/organiseMyProjects release {VERSION} "
    "-- do not edit directly -->\n"
)
PYTHON_DEPLOYMENT_COMMENT = (
    f"# deployed from Glawster/organiseMyProjects release {VERSION} "
    "-- do not edit directly\n"
)

# text templates used when creating or updating projects
GITIGNORE_CONTENT = "__pycache__/\nlogs/\n*.log\n*.pyc\n"
REQUIREMENTS_CONTENT = ""
DEV_REQUIREMENTS_CONTENT = "black\npytest\npre-commit\nruff\n"
MAIN_PY_CONTENT = """from pathlib import Path
from organiseMyProjects.logUtils import getLogger, setApplication

thisApplication = Path(__file__).parent.name
setApplication(thisApplication)

logger = getLogger(includeConsole=False)

try:
    from ui.mainMenu import mainMenu as tkinterMainMenu
except ModuleNotFoundError as exc:
    if exc.name is None or exc.name != "ui":
        raise
    tkinterMainMenu = None

try:
    from qt.mainMenu import mainMenu as qtMainMenu
except ModuleNotFoundError as exc:
    if exc.name is None or exc.name not in {"qt", "PySide6"}:
        raise
    qtMainMenu = None


def main():
    global logger

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    dryRun = not args.confirm

    logDir = Path.home() / ".local" / "state" / thisApplication
    logDir.mkdir(parents=True, exist_ok=True)

    logger = getLogger(
        logDir=logDir,
        includeConsole=True,
        dryRun=dryRun,
    )

    logger.doing("main")
    if tkinterMainMenu is not None:
        tkinterMainMenu()
    elif qtMainMenu is not None:
        qtMainMenu()
    else:
        logger.info(
            "No UI scaffold installed."
        )
    logger.done("main")


if __name__ == "__main__":
    main()
"""

PRECOMMIT_CONTENT = """default_language_version:
  python: python3

repos:
  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black

  - repo: local
    hooks:
      - id: gui-naming-linter
        name: GUI Naming Linter
        entry: runLinter
        language: python
        types: [python]
"""

PYTEST_INI_CONTENT = """[tool:pytest]
testpaths = tests
python_files = test_[a-z]*.py
python_functions = test*
python_classes = Test*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
filterwarnings = 
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
"""

VSCODE_SETTINGS_CONTENT = """{
   "python.testing.pytestEnabled": true,
   "python.testing.unittestEnabled": false,
   "python.testing.nosetestsEnabled": false,
   "python.testing.pytestArgs": [
      "tests",
      "--override-ini=python_files=test_[a-z]*.py"
   ]
}
"""

ARCHITECTURE_CONTENT = """# Architecture

## Overview

<!-- Describe the system architecture and its main responsibilities. -->

## Components

<!-- Describe the major components and their responsibilities. -->

## Dependencies and Data Flow

<!-- Describe important dependencies and how data flows through the system. -->

## Architectural Decisions

See `project/adr/` for significant architectural decisions.
"""

CURRENT_INCREMENT_CONTENT = """# Current Development Increment

## Increment

<!-- Identifier and concise name of the active increment, or None when idle. -->

## Status

Idle
<!-- Options: Active, Idle, Blocked, InReview -->

## Requirement

<!-- Governing requirement path, or None. -->

## Objective

<!-- Short description of the capability currently being delivered. -->

## Scope

<!-- Work included in the current increment. -->

## Verification

<!-- Keep only acceptance and verification still required, for example:
- [ ] Focused tests
- [ ] Full suite
- [ ] Manual acceptance
-->

## Next

<!-- Immediate next action or known next increment. Replace completed-increment
history when a new increment starts; Git retains delivery history. -->
"""

PROJECT_YAML_CONTENT = """name: "project"
description: "Project description"
version: "0.1.0"
runtime: "python3.12"
role: "standalone-application"
"""

ROADMAP_CONTENT = """# Project Roadmap

## Current Milestone

- Milestone 1: Initial core functionality.

## Future Milestones

- Milestone 2: Enhancements and integrations.
"""

REQUIREMENT_TEMPLATE_CONTENT = """# DDD: Requirement title

## Status

ToDo

## Outcome

As a <user or system>, I need <capability> so that <measurable benefit>.

## Context

Describe the current problem and relevant constraints.

## Scope

- Behaviour included in this requirement.

## Out of scope

- Closely related behaviour deliberately excluded.

## Acceptance criteria

1. Given <starting condition>, when <action>, then <observable result>.

## Dependencies and decisions

- None.

## Verification

- Planned tests or review evidence.

## Change history

- YYYY-MM-DD: created — reason or source.
"""

REQUIREMENTS_README_CONTENT = """# Requirements

Next available number: 001

## Requirement index

| Req ID | Requirement | Description | Status | Agent Prompt | Architecture Decisions |
| --- | --- | --- | --- | --- | --- |
"""

ADR_TEMPLATE_CONTENT = """# ADR-DDD: Decision title

## Status

Proposed
<!-- Options: Proposed, Accepted, Rejected, Deprecated, Superseded -->

## Context

Describe the context and problem statement that requires a decision.

## Decision Drivers

- Key consideration 1
- Key consideration 2

## Considered Options

1. Option 1
2. Option 2

## Decision Outcome

Chosen option because rationale.

### Consequences

- Positive: Benefit of choice.
- Negative: Trade-off or limitation.
"""

ADR_README_CONTENT = """# Architecture Decision Records

Next available number: 001

## Decision index

| ADR ID | Decision | Status | Date |
| --- | --- | --- | --- |
"""


def _readmeContentBuild(projectName: str) -> str:
    return f"""# {projectName}

Project scaffold created by manageProject.py.

## Documentation

- [Architecture](documentation/architecture.md)
- [Roadmap](project/roadmap.md)
- [Current Increment](project/currentIncrement.md)
- [Requirements](project/requirements/README.md)
- [Architecture Decisions](project/adr/README.md)
- [Release Guide](documentation/howToRelease.md)
- [Repository Layout](documentation/repositoryLayout.md)
- [Requirements Management](documentation/requirementsManagement.md)
- [Testing Process](documentation/testingProcess.md)
- [Master Agent Instructions](.github/agent-instructions.md)
"""


TEMPLATE_DIR = Path(__file__).resolve().parent
UI_TEMPLATE_DIR = TEMPLATE_DIR / "ui"
QT_TEMPLATE_DIR = TEMPLATE_DIR / "qt"
UI_TEMPLATE_FILES = [
    "styleUtils.py",
    "mainMenu.py",
    "baseFrame.py",
    "frameTemplate.py",
    "statusFrame.py",
]
QT_TEMPLATE_FILES = [
    "styleUtils.py",
    "mainMenu.py",
    "baseFrame.py",
    "frameTemplate.py",
    "statusFrame.py",
]
MANAGED_TEXT_TEMPLATES = [
    (Path(".pre-commit-config.yaml"), PRECOMMIT_CONTENT),
    (Path("pytest.ini"), PYTEST_INI_CONTENT),
    (Path(".vscode") / "settings.json", VSCODE_SETTINGS_CONTENT),
]
PROJECT_TEXT_TEMPLATES = [
    (Path(".gitignore"), GITIGNORE_CONTENT),
    (Path("requirements.txt"), REQUIREMENTS_CONTENT),
    (Path("dev-requirements.txt"), DEV_REQUIREMENTS_CONTENT),
    (Path("README.md"), None),
    (Path("main.py"), MAIN_PY_CONTENT),
    (Path("documentation") / "architecture.md", ARCHITECTURE_CONTENT),
    (Path("project") / "currentIncrement.md", CURRENT_INCREMENT_CONTENT),
    (Path("project") / "project.yaml", PROJECT_YAML_CONTENT),
    (Path("project") / "roadmap.md", ROADMAP_CONTENT),
    (Path("project") / "requirements" / "README.md", REQUIREMENTS_README_CONTENT),
    (
        Path("project") / "requirements" / "templates" / "requirement.md",
        REQUIREMENT_TEMPLATE_CONTENT,
    ),
    (Path("project") / "adr" / "README.md", ADR_README_CONTENT),
    (Path("project") / "adr" / "templates" / "adr.md", ADR_TEMPLATE_CONTENT),
]

PROJECT_CONTEXT_TEMPLATES = [
    (Path("documentation") / "architecture.md", ARCHITECTURE_CONTENT),
    (Path("project") / "currentIncrement.md", CURRENT_INCREMENT_CONTENT),
    (Path("project") / "project.yaml", PROJECT_YAML_CONTENT),
    (Path("project") / "roadmap.md", ROADMAP_CONTENT),
    (Path("project") / "requirements" / "README.md", REQUIREMENTS_README_CONTENT),
    (
        Path("project") / "requirements" / "templates" / "requirement.md",
        REQUIREMENT_TEMPLATE_CONTENT,
    ),
    (Path("project") / "adr" / "README.md", ADR_README_CONTENT),
    (Path("project") / "adr" / "templates" / "adr.md", ADR_TEMPLATE_CONTENT),
]
MANAGED_COPY_TEMPLATES = [
    (TEMPLATE_DIR.parent / ".github" / "AGENTS.md", Path("AGENTS.md")),
    (TEMPLATE_DIR.parent / "projectGuidelines.md", Path("projectGuidelines.md")),
    (
        TEMPLATE_DIR.parent / ".github" / "agent-instructions.md",
        Path(".github") / "agent-instructions.md",
    ),
    (
        TEMPLATE_DIR.parent / ".github" / "copilot-instructions.md",
        Path(".github") / "copilot-instructions.md",
    ),
    (
        TEMPLATE_DIR.parent / ".github" / "CLAUDE.md",
        Path("CLAUDE.md"),
    ),
    (
        TEMPLATE_DIR.parent / "documentation" / "repositoryLayout.md",
        Path("documentation") / "repositoryLayout.md",
    ),
    (
        TEMPLATE_DIR.parent / "documentation" / "requirementsManagement.md",
        Path("documentation") / "requirementsManagement.md",
    ),
    (
        TEMPLATE_DIR.parent / "documentation" / "testingProcess.md",
        Path("documentation") / "testingProcess.md",
    ),
    (
        TEMPLATE_DIR.parent / "documentation" / "howToRelease.md",
        Path("documentation") / "howToRelease.md",
    ),
    (TEMPLATE_DIR / "runLinter.py", Path("tests") / "runLinter.py"),
    (TEMPLATE_DIR / "guiNamingLinter.py", Path("tests") / "guiNamingLinter.py"),
]


def _templateModulesIterate(includeUi: bool = False, includeQt: bool = False):
    modules = [
        (TEMPLATE_DIR / "globalVars.py", Path("src") / "globalVars.py"),
        (TEMPLATE_DIR / "runLinter.py", Path("tests") / "runLinter.py"),
        (TEMPLATE_DIR / "guiNamingLinter.py", Path("tests") / "guiNamingLinter.py"),
    ]
    if includeUi:
        modules.extend(
            (UI_TEMPLATE_DIR / src_name, Path("ui") / src_name)
            for src_name in UI_TEMPLATE_FILES
        )
    if includeQt:
        modules.extend(
            (QT_TEMPLATE_DIR / src_name, Path("qt") / src_name)
            for src_name in QT_TEMPLATE_FILES
        )
    return modules


def _projectRoleDetect(basePath: Path) -> str:
    """Infer the existing project role from common repository markers."""
    if (basePath / "main.py").exists():
        return "standalone-application"

    # Inspect packaging metadata without importing or executing project-owned
    # configuration. Console entry points make the package a packaged CLI.
    pyproject = basePath / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
        except OSError:
            content = ""
        if "[project.scripts]" in content or "[project.gui-scripts]" in content:
            return "packaged-cli"

    setupCfg = basePath / "setup.cfg"
    if setupCfg.exists():
        try:
            content = setupCfg.read_text(encoding="utf-8")
        except OSError:
            content = ""
        if "console_scripts" in content:
            return "packaged-cli"

    setupPy = basePath / "setup.py"
    if setupPy.exists():
        try:
            content = setupPy.read_text(encoding="utf-8")
        except OSError:
            content = ""
        if "console_scripts" in content:
            return "packaged-cli"

        # A setup.py file is itself an unambiguous legacy Python-package
        # marker, including repositories whose package lives at the root.
        return "library"

    if (basePath / "src").exists():
        return "library"

    # A PEP 621 project without an entry point is an importable package even
    # when it uses a flat package layout rather than src/.
    if pyproject.exists() and "[project]" in content:
        return "library"

    return "unknown"


def _loadSyncModule():
    """Load syncAgentInstructions.py from the repository root path."""
    modulePath = Path(__file__).resolve().parent.parent / "syncAgentInstructions.py"
    if not modulePath.exists():
        raise RuntimeError(f"sync utility not found at {modulePath}")

    moduleSpec = importlib.util.spec_from_file_location(
        "syncAgentInstructions",
        modulePath,
    )
    if moduleSpec is None or moduleSpec.loader is None:
        raise RuntimeError("could not load sync utility module spec")

    module = importlib.util.module_from_spec(moduleSpec)
    moduleSpec.loader.exec_module(module)
    return module


def createProject(
    projectName,
    dryRun: bool = False,
    includeUi: bool = False,
    includeQt: bool = False,
):

    basePath = Path(projectName)
    if basePath.exists():
        logger.info(f"project '{projectName}' already exists")
        return

    logger.doing(f"creating project at {basePath}")

    # Create folders
    logger.action("creating directories")
    if not dryRun:
        folders = [
            "src",
            "tests",
            "logs",
            ".github",
            "documentation",
            "project",
            "project/requirements",
            "project/requirements/features",
            "project/requirements/prompt",
            "project/requirements/templates",
            "project/adr",
            "project/adr/templates",
            "project/reviews",
        ]
        if includeUi:
            folders.append("ui")
        if includeQt:
            folders.append("qt")
        for folder in folders:
            (basePath / folder).mkdir(parents=True, exist_ok=True)

        # Make directories importable packages
        (basePath / "src" / "__init__.py").touch(exist_ok=True)
        if includeUi:
            (basePath / "ui" / "__init__.py").touch(exist_ok=True)
        if includeQt:
            (basePath / "qt" / "__init__.py").touch(exist_ok=True)

    # Create core files
    logger.action("writing core files")
    if not dryRun:
        (basePath / ".gitignore").write_text(GITIGNORE_CONTENT)
        (basePath / "requirements.txt").write_text(REQUIREMENTS_CONTENT)
        (basePath / "dev-requirements.txt").write_text(DEV_REQUIREMENTS_CONTENT)
        (basePath / "README.md").write_text(_readmeContentBuild(projectName))
        (basePath / "documentation" / "architecture.md").write_text(
            ARCHITECTURE_CONTENT
        )
        (basePath / "project" / "currentIncrement.md").write_text(
            CURRENT_INCREMENT_CONTENT
        )
        (basePath / "project" / "project.yaml").write_text(PROJECT_YAML_CONTENT)
        (basePath / "project" / "roadmap.md").write_text(ROADMAP_CONTENT)
        (basePath / "project" / "requirements" / "README.md").write_text(
            REQUIREMENTS_README_CONTENT
        )
        (
            basePath / "project" / "requirements" / "templates" / "requirement.md"
        ).write_text(REQUIREMENT_TEMPLATE_CONTENT)
        (basePath / "project" / "adr" / "README.md").write_text(ADR_README_CONTENT)
        (basePath / "project" / "adr" / "templates" / "adr.md").write_text(
            ADR_TEMPLATE_CONTENT
        )

    # Copy the guidelines file
    srcGuidelines = TEMPLATE_DIR.parent / "projectGuidelines.md"
    if srcGuidelines.exists():
        logger.action("copying project guidelines")
        if not dryRun:
            (basePath / "projectGuidelines.md").write_text(
                _managedContentBuild(srcGuidelines.read_text())
            )

    # Copy the agent instructions file
    srcAgentGuidelines = TEMPLATE_DIR.parent / ".github" / "agent-instructions.md"
    if srcAgentGuidelines.exists():
        logger.action("copying agent guidelines")
        if not dryRun:
            (basePath / ".github" / "agent-instructions.md").write_text(
                _managedContentBuild(srcAgentGuidelines.read_text())
            )

    srcCopilot = TEMPLATE_DIR.parent / ".github" / "copilot-instructions.md"
    if srcCopilot.exists():
        logger.action("copying copilot shim")
        if not dryRun:
            (basePath / ".github" / "copilot-instructions.md").write_text(
                _managedContentBuild(srcCopilot.read_text())
            )

    srcClaude = TEMPLATE_DIR.parent / ".github" / "CLAUDE.md"
    if srcClaude.exists():
        logger.action("copying claude shim")
        if not dryRun:
            (basePath / "CLAUDE.md").write_text(
                _managedContentBuild(srcClaude.read_text())
            )

    # Copy the Codex agent instructions file
    srcAgentInstructions = TEMPLATE_DIR.parent / ".github" / "AGENTS.md"
    if srcAgentInstructions.exists():
        logger.action("copying agent instructions")
        if not dryRun:
            (basePath / "AGENTS.md").write_text(
                _managedContentBuild(srcAgentInstructions.read_text())
            )

    # Copy the repository layout definition
    srcRepositoryLayout = TEMPLATE_DIR.parent / "documentation" / "repositoryLayout.md"
    if srcRepositoryLayout.exists():
        logger.action("copying repository layout")
        if not dryRun:
            (basePath / "documentation" / "repositoryLayout.md").write_text(
                _managedContentBuild(srcRepositoryLayout.read_text())
            )

    # Copy the requirements management guide
    srcRequirementsManagement = (
        TEMPLATE_DIR.parent / "documentation" / "requirementsManagement.md"
    )
    if srcRequirementsManagement.exists():
        logger.action("copying requirements management guide")
        if not dryRun:
            (basePath / "documentation" / "requirementsManagement.md").write_text(
                _managedContentBuild(srcRequirementsManagement.read_text())
            )

    srcTestingProcess = TEMPLATE_DIR.parent / "documentation" / "testingProcess.md"
    if srcTestingProcess.exists():
        logger.action("copying testing process guide")
        if not dryRun:
            (basePath / "documentation" / "testingProcess.md").write_text(
                _managedContentBuild(srcTestingProcess.read_text())
            )

    # Copy the release process guide
    srcHowToRelease = TEMPLATE_DIR.parent / "documentation" / "howToRelease.md"
    if srcHowToRelease.exists():
        logger.action("copying release process guide")
        if not dryRun:
            (basePath / "documentation" / "howToRelease.md").write_text(
                _managedContentBuild(srcHowToRelease.read_text())
            )

    # Copy template modules into the new project
    logger.action("copying template modules")
    if not dryRun:
        for src, destRel in _templateModulesIterate(includeUi, includeQt):
            shutil.copy(src, basePath / destRel)

    # Create main.py starter
    logger.action("writing main.py")
    if not dryRun:
        (basePath / "main.py").write_text(MAIN_PY_CONTENT)

    # Create .pre-commit-config.yaml
    logger.action("writing .pre-commit-config.yaml")
    if not dryRun:
        (basePath / ".pre-commit-config.yaml").write_text(PRECOMMIT_CONTENT)

    # Create pytest config
    logger.action("writing pytest.ini")
    if not dryRun:
        (basePath / "pytest.ini").write_text(PYTEST_INI_CONTENT)

    # Create VSCode settings
    logger.action("writing .vscode/settings.json")
    if not dryRun:
        (basePath / ".vscode").mkdir(exist_ok=True)
        (basePath / ".vscode" / "settings.json").write_text(VSCODE_SETTINGS_CONTENT)

    # Initialize git and install pre-commit
    logger.action("initializing git repository")
    if not dryRun:
        try:
            subprocess.run(["git", "init"], cwd=basePath, check=True)
            subprocess.run(["pre-commit", "install"], cwd=basePath, check=True)
            logger.done("git initialized and pre-commit hook installed")
        except Exception as e:
            logger.error(f"Could not initialize git or install pre-commit: {e}")

    logger.done(f"project '{projectName}' created")
    if dryRun:
        logger.info("create simulation complete: no changes were applied")


def _fileCopyIfNewer(src: Path, dest: Path, dryRun: bool = False):
    if not dryRun:
        dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
        logger.action(f"updated {dest}")
        if not dryRun:
            shutil.copy(src, dest)


def _textFileUpdate(dest: Path, content: str, dryRun: bool = False):
    if not dryRun:
        dest.parent.mkdir(parents=True, exist_ok=True)
    new_bytes = content.encode("utf-8")
    existsAlready = dest.exists()
    try:
        current = dest.read_bytes() if existsAlready else None
    except OSError:
        current = None

    if current != new_bytes:
        if existsAlready:
            logger.action(f"updated {dest}")
        else:
            logger.action(f"created {dest}")
        if not dryRun:
            dest.write_bytes(new_bytes)


def _managedContentBuild(sourceContent: str, suffix: str = ".md") -> str:
    """Add the scaffold release marker to canonical managed content."""
    sourceContent, _ = _managedContentBody(sourceContent)
    if suffix != ".py":
        return DEPLOYMENT_COMMENT + sourceContent

    if sourceContent.startswith("#!"):
        shebang, separator, remainder = sourceContent.partition("\n")
        return shebang + separator + PYTHON_DEPLOYMENT_COMMENT + remainder
    return PYTHON_DEPLOYMENT_COMMENT + sourceContent


def _managedContentBody(content: str) -> tuple[str, int]:
    """Return content without leading OMP release markers and their count."""
    lines = content.splitlines(keepends=True)
    if not lines:
        return content, 0

    markerPrefixes = (
        "<!-- deployed from Glawster/organiseMyProjects release ",
        "<!-- synced from Glawster/organiseMyProjects release ",
        "# deployed from Glawster/organiseMyProjects release ",
        "# synced from Glawster/organiseMyProjects release ",
    )
    markerIndex = 1 if lines[0].startswith("#!") else 0
    markerCount = 0
    while markerIndex < len(lines) and lines[markerIndex].startswith(markerPrefixes):
        del lines[markerIndex]
        markerCount += 1

    return "".join(lines), markerCount


def _managedCopyUpdate(src: Path, dest: Path, dryRun: bool = False):
    """Deploy a managed file only when its substantive content changed."""
    managedContent = _managedContentBuild(
        src.read_text(encoding="utf-8"), suffix=dest.suffix
    )

    # A release-marker-only change would create noise without changing the
    # managed guidance or code. Preserve the marker from the release that last
    # changed the file's substantive content.
    if dest.exists():
        try:
            currentContent = dest.read_text(encoding="utf-8")
        except OSError:
            currentContent = ""
        currentBody, currentMarkerCount = _managedContentBody(currentContent)
        managedBody, _ = _managedContentBody(managedContent)
        if currentMarkerCount == 1 and currentBody == managedBody:
            return

    _textFileUpdate(
        dest,
        managedContent,
        dryRun,
    )


def _createTextFileIfMissing(dest: Path, content: str, dryRun: bool = False):
    if dest.exists():
        return
    if not dryRun:
        dest.parent.mkdir(parents=True, exist_ok=True)
    logger.action(f"created {dest}")
    if not dryRun:
        dest.write_text(content)


def _fileCopyIfMissing(src: Path, dest: Path, dryRun: bool = False):
    if dest.exists():
        return
    if not dryRun:
        dest.parent.mkdir(parents=True, exist_ok=True)
    logger.action(f"created {dest}")
    if not dryRun:
        shutil.copy(src, dest)


def migrateProject(projectName, dryRun: bool = False):
    """Add missing OMP project-management/context structures without creating application scaffolding or overwriting project-owned files."""
    basePath = Path(projectName)
    if not basePath.exists():
        logger.info(f"project '{projectName}' does not exist")
        return

    logger.doing(f"migrating project context at {basePath}")
    contextFolders = [
        "documentation",
        "project",
        "project/requirements",
        "project/requirements/features",
        "project/requirements/prompt",
        "project/requirements/templates",
        "project/adr",
        "project/adr/templates",
        "project/reviews",
    ]

    logger.action("ensuring project context directories")
    if not dryRun:
        for folder in contextFolders:
            (basePath / folder).mkdir(parents=True, exist_ok=True)

    for destRel, content in PROJECT_CONTEXT_TEMPLATES:
        _createTextFileIfMissing(basePath / destRel, content, dryRun)

    logger.done("project context migrated")
    if dryRun:
        logger.info("migration simulation complete: no changes were applied")


def _migrateManagedNames(basePath: Path, dryRun: bool = False) -> None:
    """Safely migrate only unambiguous legacy OMP-managed filenames."""
    testsPath = basePath / "tests"
    if testsPath.is_dir():
        for source in sorted(testsPath.glob("test_[A-Z]*.py")):
            concept = source.name.removeprefix("test_")
            destination = source.with_name(f"test_{concept[0].lower()}{concept[1:]}")
            if destination.exists():
                logger.info(f"test rename skipped because target exists: {destination}")
                continue
            logger.action(f"renamed {source} to {destination}")
            if not dryRun:
                source.rename(destination)

    featuresPath = basePath / "project" / "requirements" / "features"
    promptsPath = basePath / "project" / "requirements" / "prompt"
    if featuresPath.is_dir() and promptsPath.is_dir():
        for source in sorted(promptsPath.glob("*.prompt.md")):
            destination = source.with_name(source.name.replace(".prompt.md", ".md"))
            matchingFeature = featuresPath / destination.name
            if not matchingFeature.exists() or destination.exists():
                logger.info(
                    f"prompt rename skipped because mapping is ambiguous: {source}"
                )
                continue
            logger.action(f"renamed {source} to {destination}")
            if not dryRun:
                source.rename(destination)
                requirementsIndex = basePath / "project" / "requirements" / "README.md"
                if requirementsIndex.exists():
                    indexText = requirementsIndex.read_text(encoding="utf-8")
                    updatedText = indexText.replace(source.name, destination.name)
                    if updatedText != indexText:
                        requirementsIndex.write_text(updatedText, encoding="utf-8")


def updateProject(
    projectName,
    dryRun: bool = False,
    includeUi: bool = False,
    includeQt: bool = False,
):
    """Refresh managed project files while preserving project-owned scaffolds."""

    basePath = Path(projectName)
    if not basePath.exists():
        logger.info(f"project '{projectName}' does not exist")
        return

    logger.doing(f"updating project at {basePath}")
    detectedRole = _projectRoleDetect(basePath)
    logger.value("detected role", detectedRole)
    logger.action("ensuring managed directories")
    if not dryRun:
        (basePath / ".github").mkdir(parents=True, exist_ok=True)

    for destRel, content in MANAGED_TEXT_TEMPLATES:
        _textFileUpdate(basePath / destRel, content, dryRun)

    for src, destRel in MANAGED_COPY_TEMPLATES:
        if src.exists():
            _managedCopyUpdate(src, basePath / destRel, dryRun)

    # OMP 0.5 migrations are deliberately limited to deterministic legacy
    # names. Existing destinations are never overwritten.
    _migrateManagedNames(basePath, dryRun)

    logger.done("project updated")
    if dryRun:
        logger.info("update simulation complete: no changes were applied")


def main():

    global logger

    thisApplication = Path(__file__).stem
    setApplication(thisApplication)

    parser = argparse.ArgumentParser(
        description=(
            "Create, update, or sync project scaffolding/instructions. "
            "Pass the project positionally (preferred) or with --project for "
            "compatibility."
        )
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="explicitly run create mode",
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=None,
        help="Project directory name (preferred form; omit with --update to use CWD)",
    )
    parser.add_argument(
        "-p",
        "--project",
        dest="projectOption",
        default=None,
        help=(
            "Legacy named flag for the project directory name "
            "(use the positional argument instead; retained for compatibility)"
        ),
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Refresh an existing project instead of creating a new one",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help=(
            "adopt missing OMP project-management/context structures without "
            "creating application scaffolding or overwriting project-owned files"
        ),
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="sync shared instruction files to downstream repositories",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="install tkinter UI templates in a ui package",
    )
    parser.add_argument(
        "-qt",
        "--qt",
        action="store_true",
        help="install Qt UI templates in a qt package",
    )
    parser.add_argument(
        "-y",
        "--confirm",
        dest="confirm",
        action="store_true",
        help="execute changes (default is dry-run)",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="with --sync: create and merge conflict-free sync pull requests",
    )
    parser.add_argument(
        "--repo",
        nargs="?",
        const="",
        default=None,
        metavar="OWNER/REPO",
        help=(
            "with --sync: sync one repository; omit value to choose from a "
            "numbered list"
        ),
    )
    parser.add_argument(
        "--token",
        default=None,
        help="with --sync: GitHub PAT (overrides GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="with --sync: show detailed output for each repository",
    )

    args = parser.parse_args()
    dryRun = not args.confirm

    if args.project is not None and args.projectOption is not None:
        parser.error(
            "Use either the positional project argument or the --project flag, not both."
        )
    modeCount = sum(
        [bool(args.create), bool(args.update), bool(args.migrate), bool(args.sync)]
    )
    if modeCount > 1:
        parser.error(
            "Use only one mode at a time: --create, --update, --migrate, or --sync."
        )

    if args.sync and (args.ui or args.qt):
        parser.error("--sync does not support --ui or --qt.")
    if args.migrate and (args.ui or args.qt):
        parser.error("--migrate does not support --ui or --qt.")

    projectPath = args.project if args.project is not None else args.projectOption

    logDir = Path.home() / ".local" / "state" / thisApplication
    logDir.mkdir(parents=True, exist_ok=True)

    logger = getLogger(
        logDir=logDir,
        includeConsole=True,
        dryRun=dryRun,
    )
    logger.value("OMP version", VERSION)
    logger.doing(thisApplication)

    if args.sync:
        # Delegate sync workflow to the existing sync utility.
        syncAgentInstructions = _loadSyncModule()

        syncArgv = ["syncAgentInstructions.py"]
        if args.confirm:
            syncArgv.append("--confirm")
        if args.merge:
            syncArgv.append("--merge")
        if args.repo is not None:
            syncArgv.append("--repo")
            if args.repo:
                syncArgv.append(args.repo)
        if args.token:
            syncArgv.extend(["--token", args.token])
        if args.verbose:
            syncArgv.append("--verbose")

        originalArgv = sys.argv
        try:
            sys.argv = syncArgv
            syncAgentInstructions.main()
        finally:
            sys.argv = originalArgv
        return

    if args.migrate:
        project_path = projectPath or Path.cwd()
        migrateProject(project_path, dryRun=dryRun)
    elif args.update:
        project_path = projectPath or Path.cwd()
        updateProject(
            project_path,
            dryRun=dryRun,
            includeUi=args.ui,
            includeQt=args.qt,
        )
    else:
        if args.create is False and projectPath is None:
            parser.error(
                "Provide a project for create mode, or use "
                "--update/--migrate/--sync explicitly."
            )
        if projectPath is None:
            parser.error("the following arguments are required: project")
        createProject(
            projectPath,
            dryRun=dryRun,
            includeUi=args.ui,
            includeQt=args.qt,
        )


if __name__ == "__main__":
    main()
