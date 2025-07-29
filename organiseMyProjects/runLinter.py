"""
runLinter.py - Entry point for GUI Naming Linter

This script allows you to run guiNamingLinter.py via the command line.

Usage:
    python runLinter.py my_script.py
"""

import sys
from organiseMyProjects.guiNamingLinter import lint_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python runLinter.py <path-to-python-file>")
        return

    filepath = sys.argv[1]
    print(f"Linting: {filepath}")
    lint_file(filepath)

if __name__ == "__main__":
    main()
