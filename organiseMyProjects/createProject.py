import os
import shutil
import subprocess

from pathlib import Path

def createProject(projectName):
    basePath = Path(projectName)
    if basePath.exists():
        print(f"Project '{projectName}' already exists.")
        return

    # Create folders
    (basePath / "src").mkdir(parents=True)
    (basePath / "tests").mkdir()
    (basePath / "logs").mkdir()

    # Create core files
    (basePath / ".gitignore").write_text("__pycache__/\nlogs/\n*.log\n*.pyc\n")
    (basePath / "requirements.txt").write_text("pywin32\n")
    (basePath / "dev-requirements.txt").write_text("black\npytest\npre-commit\n")
    (basePath / "README.md").write_text(f"# {projectName}\n\nProject scaffold created by createProject.py\n")

    # Copy the guidelines file
    srcGuidelines = Path("projectGuidelines.md")
    if srcGuidelines.exists():
        shutil.copy(srcGuidelines, basePath / "projectGuidelines.md")

    # Create main.py starter
    mainPath = basePath / "src" / "main.py"
    mainPath.write_text("""from setupLogging import setupLogging

logger = setupLogging("main")

def main():
    logger.info("...starting main script")
    print("Main script running.")

if __name__ == "__main__":
    main()
""")

    # Create setupLogging.py
    loggingPath = basePath / "src" / "setupLogging.py"
    loggingPath.write_text("""import os
import logging
import datetime

def setupLogging(title: str) -> logging.Logger:
    title = title.replace(" ", "")
    logger = logging.getLogger(title)
    if not logger.handlers:
        logDir = os.getcwd()
        os.makedirs(logDir, exist_ok=True)
        logDate = datetime.datetime.now().strftime("%Y%m%d")
        logFilePath = os.path.join(logDir, f"{title}.{logDate}.log")

        handler = logging.FileHandler(logFilePath)
        formatter = logging.Formatter('%(asctime)s [%(module)s] %(levelname)s %(message)s')
        handler.setFormatter(formatter)

        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

    return logger
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
        entry: python guiNamingLinter.py src/
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
