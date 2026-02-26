import datetime
import os
import shutil
import subprocess
import argparse
from pathlib import Path

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

PRECOMMIT_CONTENT = """repos:
  - repo: https://github.com/psf/black
    rev: stable
    hooks:
      - id: black
        language: system
  - repo: local
    hooks:
      - id: gui-naming-linter
        name: GUI Naming Linter
        entry: python tests/runLinter.py
        language: system
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

def createProject(projectName):

    basePath = Path(projectName)
    if basePath.exists():
        print(f"Project '{projectName}' already exists.")
        return

    print(f"Creating project at {basePath}...")

    # Create folders
    print("Creating directories...")
    (basePath / "src").mkdir(parents=True)
    (basePath / "ui").mkdir()
    (basePath / "tests").mkdir()
    (basePath / "logs").mkdir()
    (basePath / ".github").mkdir()

    # Make directories importable packages
    (basePath / "src" / "__init__.py").touch()
    (basePath / "ui" / "__init__.py").touch()

    # Create core files
    print("Writing core files...")
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
        print("Copying project guidelines...")
        shutil.copy(srcGuidelines, basePath / "projectGuidelines.md")

    # Copy the copilot instructions file
    srcCopilotInstructions = TEMPLATE_DIR.parent / ".github" / "copilot-instructions.md"
    if srcCopilotInstructions.exists():
        print("Copying copilot instructions...")
        shutil.copy(srcCopilotInstructions, basePath / ".github" / "copilot-instructions.md")

    # Copy template modules into the new project
    print("Copying template modules...")
    shutil.copy(TEMPLATE_DIR / "globalVars.py", basePath / "src" / "globalVars.py")
    shutil.copy(TEMPLATE_DIR / "styleUtils.py", basePath / "ui" / "styleUtils.py")
    shutil.copy(TEMPLATE_DIR / "mainMenu.py", basePath / "ui" / "mainMenu.py")
    shutil.copy(TEMPLATE_DIR / "baseFrame.py", basePath / "ui" / "baseFrame.py")
    shutil.copy(TEMPLATE_DIR / "frameTemplate.py", basePath / "ui" / "frameTemplate.py")
    shutil.copy(TEMPLATE_DIR / "statusFrame.py", basePath / "ui" / "statusFrame.py")
    shutil.copy(TEMPLATE_DIR / "runLinter.py", basePath / "tests" / "runLinter.py")
    shutil.copy(TEMPLATE_DIR / "guiNamingLinter.py", basePath / "tests" / "guiNamingLinter.py")

    # Create main.py starter
    mainPath = basePath / "main.py"
    mainPath.write_text(MAIN_PY_CONTENT)

    # Create .pre-commit-config.yaml
    preCommitPath = basePath / ".pre-commit-config.yaml"
    preCommitPath.write_text(PRECOMMIT_CONTENT)

    # Create pytest config
    (basePath / "pytest.ini").write_text(PYTEST_INI_CONTENT)

    # Create VSCode settings
    (basePath / ".vscode").mkdir(exist_ok=True)
    (basePath / ".vscode" / "settings.json").write_text(VSCODE_SETTINGS_CONTENT)

    # Initialize git and install pre-commit
    try:
        print("Initializing git repository...")
        subprocess.run(["git", "init"], cwd=basePath, check=True)
        subprocess.run(["pre-commit", "install"], cwd=basePath, check=True)
        print("Git initialized and pre-commit hook installed.")
    except Exception as e:
        print(f"Could not initialize git or install pre-commit: {e}")

    print(f"Project '{projectName}' created with full structure.")


def _backup_file(dest: Path) -> None:
    """Rename dest to {stem}.YYMMDD{suffix} before overwriting."""
    if dest.exists():
        stamp = datetime.date.today().strftime("%y%m%d")
        backup = dest.with_name(f"{dest.stem}.{stamp}{dest.suffix}")
        dest.rename(backup)
        print(f"Backed up {dest.name} → {backup.name}")


def _copy_if_newer(src: Path, dest: Path):

    """Copy src to dest if dest doesn't exist or src is newer."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
        _backup_file(dest)
        shutil.copy(src, dest)
        print(f"Updated {dest}")


def _update_text_file(dest: Path, content: str):

    """Write *content* to *dest* if the file is missing or differs.

    Uses binary comparison to avoid encoding issues on Windows where
    the default text encoding may not be UTF-8.
    """

    dest.parent.mkdir(parents=True, exist_ok=True)
    new_bytes = content.encode("utf-8")
    try:
        current = dest.read_bytes() if dest.exists() else None
    except OSError:
        current = None

    if current != new_bytes:
        _backup_file(dest)
        dest.write_bytes(new_bytes)
        print(f"Updated {dest}")


def updateProject(projectName):

    basePath = Path(projectName)
    if not basePath.exists():
        print(f"Project '{projectName}' does not exist.")
        return

    print(f"Updating project at {basePath}...")
    print("Ensuring directories and packages...")

    for folder in ["src", "ui", "tests", "logs", ".github"]:
        (basePath / folder).mkdir(parents=True, exist_ok=True)

    (basePath / "src" / "__init__.py").touch(exist_ok=True)
    (basePath / "ui" / "__init__.py").touch(exist_ok=True)

    _update_text_file(basePath / ".gitignore", GITIGNORE_CONTENT)
    _update_text_file(basePath / "requirements.txt", REQUIREMENTS_CONTENT)
    _update_text_file(basePath / "dev-requirements.txt", DEV_REQUIREMENTS_CONTENT)
    _update_text_file(basePath / ".env", ENV_CONTENT)
    _update_text_file(
        basePath / "README.md",
        f"# {projectName}\n\nProject scaffold created by createProject.py\n",
    )

    srcGuidelines = TEMPLATE_DIR.parent / "projectGuidelines.md"
    if srcGuidelines.exists():
        print("Checking guidelines file...")
        _copy_if_newer(srcGuidelines, basePath / "projectGuidelines.md")

    srcCopilotInstructions = TEMPLATE_DIR.parent / ".github" / "copilot-instructions.md"
    if srcCopilotInstructions.exists():
        print("Checking copilot instructions...")
        _copy_if_newer(srcCopilotInstructions, basePath / ".github" / "copilot-instructions.md")

    print("Checking template modules...")
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
        _copy_if_newer(TEMPLATE_DIR / src_name, basePath / dest_rel)

    _update_text_file(basePath / "main.py", MAIN_PY_CONTENT)
    _update_text_file(basePath / ".pre-commit-config.yaml", PRECOMMIT_CONTENT)
    _update_text_file(basePath / "pytest.ini", PYTEST_INI_CONTENT)
    (basePath / ".vscode").mkdir(parents=True, exist_ok=True)
    _update_text_file(basePath / ".vscode" / "settings.json", VSCODE_SETTINGS_CONTENT)

    print(f"Project '{projectName}' updated.")

def main():
    
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

    args = parser.parse_args()

    if args.update:
        project_path = args.project or Path.cwd()
        updateProject(project_path)
    else:
        if args.project is None:
            parser.error("the following arguments are required: project")
        createProject(args.project)


if __name__ == '__main__':
    main()
