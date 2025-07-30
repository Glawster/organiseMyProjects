import os
import shutil
import subprocess

from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent

def createProject(projectName):
    basePath = Path(projectName)
    if basePath.exists():
        print(f"Project '{projectName}' already exists.")
        return

    # Create folders
    (basePath / "src").mkdir(parents=True)
    (basePath / "ui").mkdir()
    (basePath / "tests").mkdir()
    (basePath / "logs").mkdir()

    # Make directories importable packages
    (basePath / "src" / "__init__.py").touch()
    (basePath / "ui" / "__init__.py").touch()

    # Create core files
    (basePath / ".gitignore").write_text("__pycache__/\nlogs/\n*.log\n*.pyc\n")
    (basePath / "requirements.txt").write_text("pywin32\n")
    (basePath / "dev-requirements.txt").write_text("black\npytest\npre-commit\n")
    (basePath / "README.md").write_text(f"# {projectName}\n\nProject scaffold created by createProject.py\n")

    # Copy the guidelines file
    srcGuidelines = Path("projectGuidelines.md")
    if srcGuidelines.exists():
        shutil.copy(srcGuidelines, basePath / "projectGuidelines.md")

    # Copy helper modules into the new project
    shutil.copy(TEMPLATE_DIR / "logUtils.py", basePath / "src" / "logUtils.py")
    shutil.copy(TEMPLATE_DIR / "styleUtils.py", basePath / "ui" / "styleUtils.py")
    shutil.copy(TEMPLATE_DIR / "mainMenu.py", basePath / "ui" / "mainMenu.py")
    shutil.copy(TEMPLATE_DIR / "frameTemplate.py", basePath / "ui" / "frameTemplate.py")
    shutil.copy(TEMPLATE_DIR / "runLinter.py", basePath / "tests" / "runLinter.py")
    shutil.copy(TEMPLATE_DIR / "guiNamingLinter.py", basePath / "tests" / "guiNamingLinter.py")

    # Create main.py starter
    mainPath = basePath / "src" / "main.py"
    mainPath.write_text("""from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from logUtils import setupLogging
from ui.mainMenu import mainMenu

logger = setupLogging("main")

def main():
    logger.info("...starting main script")
    mainMenu()

if __name__ == "__main__":
    main()
""")

    # Create .pre-commit-config.yaml
    preCommitPath = basePath / ".pre-commit-config.yaml"
    preCommitPath.write_text("""repos:
  - repo: https://github.com/psf/black
    rev: stable
    hooks:
      - id: black
  - repo: local
    hooks:
      - id: gui-naming-linter
        name: GUI Naming Linter
        entry: runLinter src/
        language: system
        types: [python]
""")

    # Initialize git and install pre-commit
    try:
        subprocess.run(["git", "init"], cwd=basePath, check=True)
        subprocess.run(["pre-commit", "install"], cwd=basePath, check=True)
        print("Git initialized and pre-commit hook installed.")
    except Exception as e:
        print(f"Could not initialize git or install pre-commit: {e}")

    print(f"Project '{projectName}' created with full structure.")

def main():

    import sys
    if len(sys.argv) < 2:
        print("Usage: python createProject.py <project_name>")
    else:
        createProject(sys.argv[1])


if __name__ == '__main__':
    main()
