import datetime
import os
import shutil
import subprocess
import argparse
from pathlib import Path

from organiseMyProjects.logUtils import getLogger, setApplication

thisApplication = Path(__file__).stem
setApplication(thisApplication)
logger = getLogger(includeConsole=False)

# text templates used when creating or updating projects
GITIGNORE_CONTENT = "__pycache__/\nlogs/\n*.log\n*.pyc\n"
REQUIREMENTS_CONTENT = "pywin32\n"
DEV_REQUIREMENTS_CONTENT = "black\npytest\npre-commit\n"
MAIN_PY_CONTENT = """from pathlib import Path
from organiseMyProjects.logUtils import getLogger, setApplication

thisApplication = Path(__file__).parent.name
setApplication(thisApplication)

logger = getLogger(includeConsole=False)

try:
    from ui.mainMenu import mainMenu as tkinterMainMenu
except ImportError:
    tkinterMainMenu = None

try:
    from Qt.mainMenu import mainMenu as qtMainMenu
except ImportError:
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
        logger.info("No UI scaffold installed. Run createProject --update --ui and/or createProject --update -qt to add GUI templates.")
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
python_files = test[!_]*.py
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
      "--override-ini=python_files=test[a-zA-Z]*.py"
   ]
}
"""

TEMPLATE_DIR = Path(__file__).resolve().parent
UI_TEMPLATE_DIR = TEMPLATE_DIR / "ui"
QT_TEMPLATE_DIR = TEMPLATE_DIR / "Qt"
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


def _build_env_content(includeUi: bool = False, includeQt: bool = False) -> str:
    pythonPaths = ["src"]
    if includeUi:
        pythonPaths.append("ui")
    if includeQt:
        pythonPaths.append("Qt")
    return f"PYTHONPATH={';'.join(pythonPaths)}\n"


def _iter_template_modules(includeUi: bool = False, includeQt: bool = False):
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
            (QT_TEMPLATE_DIR / src_name, Path("Qt") / src_name)
            for src_name in QT_TEMPLATE_FILES
        )
    return modules


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
        (basePath / "src").mkdir(parents=True)
        (basePath / "tests").mkdir()
        (basePath / "logs").mkdir()
        (basePath / ".github").mkdir()
        if includeUi:
            (basePath / "ui").mkdir()
        if includeQt:
            (basePath / "Qt").mkdir()

        # Make directories importable packages
        (basePath / "src" / "__init__.py").touch()
        if includeUi:
            (basePath / "ui" / "__init__.py").touch()
        if includeQt:
            (basePath / "Qt" / "__init__.py").touch()

    # Create core files
    logger.action("writing core files")
    if not dryRun:
        (basePath / ".gitignore").write_text(GITIGNORE_CONTENT)
        (basePath / "requirements.txt").write_text(REQUIREMENTS_CONTENT)
        (basePath / "dev-requirements.txt").write_text(DEV_REQUIREMENTS_CONTENT)
        (basePath / ".env").write_text(_build_env_content(includeUi, includeQt))
        (basePath / "README.md").write_text(
            f"# {projectName}\n\nProject scaffold created by createProject.py\n"
        )

    # Copy the guidelines file
    srcGuidelines = TEMPLATE_DIR.parent / "projectGuidelines.md"
    if srcGuidelines.exists():
        logger.action("copying project guidelines")
        if not dryRun:
            shutil.copy(srcGuidelines, basePath / "projectGuidelines.md")

    # Copy the copilot instructions file
    srcCopilotInstructions = TEMPLATE_DIR.parent / ".github" / "copilot-instructions.md"
    if srcCopilotInstructions.exists():
        logger.action("copying copilot instructions")
        if not dryRun:
            shutil.copy(srcCopilotInstructions, basePath / ".github" / "copilot-instructions.md")

    # Copy template modules into the new project
    logger.action("copying template modules")
    if not dryRun:
        for src, destRel in _iter_template_modules(includeUi, includeQt):
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


def _backup_file(dest: Path, dryRun: bool = False) -> None:
    if dest.exists():
        stamp = datetime.date.today().strftime("%y%m%d")
        backup = dest.with_name(f"{dest.stem}.{stamp}{dest.suffix}")
        logger.action(f"backed up {dest.name} → {backup.name}")
        if not dryRun:
            dest.rename(backup)


def _copy_if_newer(src: Path, dest: Path, dryRun: bool = False):
    if not dryRun:
        dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
        _backup_file(dest, dryRun)
        logger.action(f"updated {dest}")
        if not dryRun:
            shutil.copy(src, dest)


def _update_text_file(dest: Path, content: str, dryRun: bool = False):
    if not dryRun:
        dest.parent.mkdir(parents=True, exist_ok=True)
    new_bytes = content.encode("utf-8")
    try:
        current = dest.read_bytes() if dest.exists() else None
    except OSError:
        current = None

    if current != new_bytes:
        _backup_file(dest, dryRun)
        logger.action(f"updated {dest}")
        if not dryRun:
            dest.write_bytes(new_bytes)


def updateProject(
    projectName,
    dryRun: bool = False,
    includeUi: bool = False,
    includeQt: bool = False,
):

    basePath = Path(projectName)
    if not basePath.exists():
        logger.info(f"project '{projectName}' does not exist")
        return

    logger.doing(f"updating project at {basePath}")
    installUi = includeUi or (basePath / "ui").exists()
    installQt = includeQt or (basePath / "Qt").exists()
    logger.action("ensuring directories and packages")
    if not dryRun:
        folders = ["src", "tests", "logs", ".github"]
        if installUi:
            folders.append("ui")
        if installQt:
            folders.append("Qt")
        for folder in folders:
            (basePath / folder).mkdir(parents=True, exist_ok=True)

        (basePath / "src" / "__init__.py").touch(exist_ok=True)
        if installUi:
            (basePath / "ui" / "__init__.py").touch(exist_ok=True)
        if installQt:
            (basePath / "Qt" / "__init__.py").touch(exist_ok=True)

    _update_text_file(basePath / ".gitignore", GITIGNORE_CONTENT, dryRun)
    _update_text_file(basePath / "requirements.txt", REQUIREMENTS_CONTENT, dryRun)
    _update_text_file(basePath / "dev-requirements.txt", DEV_REQUIREMENTS_CONTENT, dryRun)
    _update_text_file(basePath / ".env", _build_env_content(installUi, installQt), dryRun)
    _update_text_file(
        basePath / "README.md",
        f"# {projectName}\n\nProject scaffold created by createProject.py\n",
        dryRun,
    )

    srcGuidelines = TEMPLATE_DIR.parent / "projectGuidelines.md"
    if srcGuidelines.exists():
        logger.info("checking guidelines file")
        _copy_if_newer(srcGuidelines, basePath / "projectGuidelines.md", dryRun)

    srcCopilotInstructions = TEMPLATE_DIR.parent / ".github" / "copilot-instructions.md"
    if srcCopilotInstructions.exists():
        logger.info("checking copilot instructions")
        _copy_if_newer(srcCopilotInstructions, basePath / ".github" / "copilot-instructions.md", dryRun)

    logger.info("checking template modules")
    for src, destRel in _iter_template_modules(installUi, installQt):
        _copy_if_newer(src, basePath / destRel, dryRun)

    _update_text_file(basePath / "main.py", MAIN_PY_CONTENT, dryRun)
    _update_text_file(basePath / ".pre-commit-config.yaml", PRECOMMIT_CONTENT, dryRun)
    _update_text_file(basePath / "pytest.ini", PYTEST_INI_CONTENT, dryRun)
    if not dryRun:
        (basePath / ".vscode").mkdir(parents=True, exist_ok=True)
    _update_text_file(basePath / ".vscode" / "settings.json", VSCODE_SETTINGS_CONTENT, dryRun)

    logger.done(f"project '{projectName}' updated")


def main():
    global logger

    thisApplication = Path(__file__).stem
    setApplication(thisApplication)

    parser = argparse.ArgumentParser(
        description="Create or update a project scaffold"
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=None,
        help="Name of the project directory (omit with --update to use CWD)",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Refresh an existing project instead of creating a new one",
    )
    parser.add_argument(
        "-ui",
        "--ui",
        action="store_true",
        help="install tkinter UI templates in a ui package",
    )
    parser.add_argument(
        "-qt",
        "--qt",
        action="store_true",
        help="install Qt UI templates in a Qt package",
    )
    parser.add_argument(
        "--confirm",
        dest="confirm",
        action="store_true",
        help="execute changes (default is dry-run)",
    )

    args = parser.parse_args()
    dryRun = not args.confirm

    logDir = Path.home() / ".local" / "state" / thisApplication
    logDir.mkdir(parents=True, exist_ok=True)

    logger = getLogger(
        logDir=logDir,
        includeConsole=True,
        dryRun=dryRun,
    )
    logger.doing(thisApplication)

    if args.update:
        project_path = args.project or Path.cwd()
        updateProject(
            project_path,
            dryRun=dryRun,
            includeUi=args.ui,
            includeQt=args.qt,
        )
    else:
        if args.project is None:
            parser.error("the following arguments are required: project")
        createProject(
            args.project,
            dryRun=dryRun,
            includeUi=args.ui,
            includeQt=args.qt,
        )


if __name__ == '__main__':
    main()
