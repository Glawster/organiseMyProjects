"""CLI entry point for the GUI Naming Linter."""

import argparse
import os

from organiseMyProjects.guiNamingLinter import lintFile, lintGuiNaming


def _lint_target(target: str) -> None:
    """Lint a single file or directory."""
    print(f"Linting: {target}")
    if os.path.isdir(target):
        lintGuiNaming(target)
    else:
        lintFile(target)


def main() -> None:
    
    parser = argparse.ArgumentParser(
        description="Run the GUI naming linter on files or directories"
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="File or directory to lint; defaults to the current project",
    )
    args = parser.parse_args()

    for target in args.targets:
        if not os.path.exists(target):
            print(f"Target '{target}' does not exist. Skipping...")
            continue
        if not os.access(target, os.R_OK):
            print(f"Target '{target}' is not readable. Skipping...")
            continue
        if not os.path.isdir(target) and not target.endswith(".py"):
            print(f"Target '{target}' is not a Python file or directory. Skipping...")
            continue
        _lint_target(target)

    # No path provided; lint the project structure from the CWD
    print("No target supplied. Searching for project directories to lint...")
    found = False
    for folder in ("src", "ui", "tests"):
        if os.path.isdir(folder):
            _lint_target(folder)
            found = True

    if not found:
        _lint_target(".")

if __name__ == "__main__":
    main()
