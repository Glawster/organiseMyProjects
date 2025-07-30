"""
runLinter.py - Entry point for GUI Naming Linter

This script exposes the GUI naming linter as a command line tool.

Usage:
    runLinter <file_or_dir>
"""

import os
import sys
from organiseMyProjects.guiNamingLinter import lintFile, lintGuiNaming

def main():
    if len(sys.argv) < 2:
        print("Usage: runLinter <file_or_dir>")
        return

    target = sys.argv[1]
    print(f"Linting: {target}")

    if os.path.isdir(target):
        lintGuiNaming(target)
    else:
        lintFile(target)

if __name__ == "__main__":
    main()
