import os
import shutil
import subprocess
import argparse
try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    from importlib_resources import files

from pathlib import Path

# text templates used when creating or updating projects
GITIGNORE_CONTENT = "__pycache__/\nlogs/\n*.log\n*.pyc\n"
REQUIREMENTS_CONTENT = "pywin32\n"
DEV_REQUIREMENTS_CONTENT = "black\npytest\npre-commit\n"
ENV_CONTENT = "PYTHONPATH=src;ui\n"
MAIN_PY_CONTENT = """from src.logUtils import setupLogging
from ui.mainMenu import mainMenu

logger = setupLogging("main")

def main():
    logger.info("...starting main script")
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
    try:
        templateFiles = files('organiseMyProjects') / 'templates'
        copilot_instructions_file = templateFiles / 'copilot-instructions.md'
        if copilot_instructions_file.is_file():
            print("Copying copilot instructions...")
            copilot_instructions_content = copilot_instructions_file.read_text()
            (basePath / ".github" / "copilot-instructions.md").write_text(copilot_instructions_content)
        else:
            raise FileNotFoundError("Template not found in package")
    except (ImportError, FileNotFoundError):
        # Fallback to file system if package resource not available (development mode)
        srcCopilotInstructions = TEMPLATE_DIR.parent / ".github" / "copilot-instructions.md"
        if srcCopilotInstructions.exists():
            print("Copying copilot instructions...")
            shutil.copy(srcCopilotInstructions, basePath / ".github" / "copilot-instructions.md")

    # Copy helper modules into the new project
    print("Copying template modules...")
    shutil.copy(TEMPLATE_DIR / "logUtils.py", basePath / "src" / "logUtils.py")
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

    # Initialize git and install pre-commit
    try:
        print("Initializing git repository...")
        subprocess.run(["git", "init"], cwd=basePath, check=True)
        subprocess.run(["pre-commit", "install"], cwd=basePath, check=True)
        print("Git initialized and pre-commit hook installed.")
    except Exception as e:
        print(f"Could not initialize git or install pre-commit: {e}")

    print(f"Project '{projectName}' created with full structure.")


def _copy_if_newer(src: Path, dest: Path):

    """Copy src to dest if dest doesn't exist or src is newer."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
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

    try:
        template_files = files('organiseMyProjects') / 'templates'
        copilot_instructions_file = template_files / 'copilot-instructions.md'
        if copilot_instructions_file.is_file():
            print("Checking copilot instructions...")
            copilot_instructions_content = copilot_instructions_file.read_text()
            current_content = ""
            dest_file = basePath / ".github" / "copilot-instructions.md"
            if dest_file.exists():
                current_content = dest_file.read_text()
            if current_content != copilot_instructions_content:
                dest_file.write_text(copilot_instructions_content)
                print(f"Updated {dest_file}")
        else:
            raise FileNotFoundError("Template not found in package")
    except (ImportError, FileNotFoundError):
        # Fallback to file system if package resource not available (development mode)
        srcCopilotInstructions = TEMPLATE_DIR.parent / ".github" / "copilot-instructions.md"
        if srcCopilotInstructions.exists():
            print("Checking copilot instructions...")
            _copy_if_newer(srcCopilotInstructions, basePath / ".github" / "copilot-instructions.md")

    print("Checking template modules...")
    modules = [
        ("logUtils.py", "src/logUtils.py"),
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
