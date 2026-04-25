import datetime
import os
import shutil
import subprocess
import argparse
from pathlib import Path

from organiseMyProjects.logUtils import getLogger, thisApplication

logger = getLogger(thisApplication, includeConsole=False)  # placeholder; re-initialised with Path(__file__).stem in main()

# text templates used when creating or updating projects
GITIGNORE_CONTENT = "__pycache__/\nlogs/\n*.log\n*.pyc\n"
REQUIREMENTS_CONTENT = "pywin32\n"
DEV_REQUIREMENTS_CONTENT = "black\npytest\npre-commit\n"
ENV_CONTENT = "PYTHONPATH=src;ui\n"
MAIN_PY_CONTENT = """from ui.mainMenu import mainMenu

def main():
    print("Starting application...")
    mainMenu()

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

def createProject(projectName, dryRun: bool = False):

    basePath = Path(projectName)
    if basePath.exists():
        logger.info(f"project '{projectName}' already exists")
        return

    logger.doing(f"creating project at {basePath}")

    # Create folders
    logger.action("creating directories")
    if not dryRun:
        (basePath / "src").mkdir(parents=True)
        (basePath / "ui").mkdir()
        (basePath / "tests").mkdir()
        (basePath / "logs").mkdir()
        (basePath / ".github").mkdir()

        # Make directories importable packages
        (basePath / "src" / "__init__.py").touch()
        (basePath / "ui" / "__init__.py").touch()

    # Create core files
    logger.action("writing core files")
    if not dryRun:
        (basePath / ".gitignore").write_text(GITIGNORE_CONTENT)
        (basePath / "requirements.txt").write_text(REQUIREMENTS_CONTENT)
        (basePath / "dev-requirements.txt").write_text(DEV_REQUIREMENTS_CONTENT)
        (basePath / ".env").write_text(ENV_CONTENT)
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
        shutil.copy(TEMPLATE_DIR / "globalVars.py", basePath / "src" / "globalVars.py")
        shutil.copy(TEMPLATE_DIR / "styleUtils.py", basePath / "ui" / "styleUtils.py")
        shutil.copy(TEMPLATE_DIR / "mainMenu.py", basePath / "ui" / "mainMenu.py")
        shutil.copy(TEMPLATE_DIR / "baseFrame.py", basePath / "ui" / "baseFrame.py")
        shutil.copy(TEMPLATE_DIR / "frameTemplate.py", basePath / "ui" / "frameTemplate.py")
        shutil.copy(TEMPLATE_DIR / "statusFrame.py", basePath / "ui" / "statusFrame.py")
        shutil.copy(TEMPLATE_DIR / "runLinter.py", basePath / "tests" / "runLinter.py")
        shutil.copy(TEMPLATE_DIR / "guiNamingLinter.py", basePath / "tests" / "guiNamingLinter.py")

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
    """Rename dest to {stem}.YYMMDD{suffix} before overwriting."""
    if dest.exists():
        stamp = datetime.date.today().strftime("%y%m%d")
        backup = dest.with_name(f"{dest.stem}.{stamp}{dest.suffix}")
        logger.action(f"backed up {dest.name} → {backup.name}")
        if not dryRun:
            dest.rename(backup)


def _copy_if_newer(src: Path, dest: Path, dryRun: bool = False):

    """Copy src to dest if dest doesn't exist or src is newer."""
    if not dryRun:
        dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
        _backup_file(dest, dryRun)
        logger.action(f"updated {dest}")
        if not dryRun:
            shutil.copy(src, dest)


def _update_text_file(dest: Path, content: str, dryRun: bool = False):

    """Write *content* to *dest* if the file is missing or differs.

    Uses binary comparison to avoid encoding issues on Windows where
    the default text encoding may not be UTF-8.
    """

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


def updateProject(projectName, dryRun: bool = False):

    basePath = Path(projectName)
    if not basePath.exists():
        logger.info(f"project '{projectName}' does not exist")
        return

    logger.doing(f"updating project at {basePath}")
    logger.action("ensuring directories and packages")
    if not dryRun:
        for folder in ["src", "ui", "tests", "logs", ".github"]:
            (basePath / folder).mkdir(parents=True, exist_ok=True)

        (basePath / "src" / "__init__.py").touch(exist_ok=True)
        (basePath / "ui" / "__init__.py").touch(exist_ok=True)

    _update_text_file(basePath / ".gitignore", GITIGNORE_CONTENT, dryRun)
    _update_text_file(basePath / "requirements.txt", REQUIREMENTS_CONTENT, dryRun)
    _update_text_file(basePath / "dev-requirements.txt", DEV_REQUIREMENTS_CONTENT, dryRun)
    _update_text_file(basePath / ".env", ENV_CONTENT, dryRun)
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
    modules = [
        ("globalVars.py", "src/globalVars.py"),
        ("styleUtils.py", "ui/styleUtils.py"),
        ("mainMenu.py", "ui/mainMenu.py"),
        ("baseFrame.py", "ui/baseFrame.py"),
        ("frameTemplate.py", "ui/frameTemplate.py"),
        ("statusFrame.py", "ui/statusFrame.py"),
        ("runLinter.py", "tests/runLinter.py"),
        ("guiNamingLinter.py", "tests/guiNamingLinter.py"),
    ]
    for src_name, dest_rel in modules:
        _copy_if_newer(TEMPLATE_DIR / src_name, basePath / dest_rel, dryRun)

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
        "--confirm",
        dest="confirm",
        action="store_true",
        help="execute changes (default is dry-run)",
    )

    args = parser.parse_args()
    dryRun = not args.confirm
    print (thisApplication)
    logger = getLogger(thisApplication, includeConsole=True, dryRun=dryRun)
    logger.doing(thisApplication)

    if args.update:
        project_path = args.project or Path.cwd()
        updateProject(project_path, dryRun=dryRun)
    else:
        if args.project is None:
            parser.error("the following arguments are required: project")
        createProject(args.project, dryRun=dryRun)


if __name__ == '__main__':
    main()
