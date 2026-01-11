"""organiseMyProjects - Python project scaffolding toolkit.

This package provides tools to create and manage Python projects with:
- Predefined project structure
- GUI framework components
- Naming convention linters
- Development guidelines

Main components:
- createProject: Project scaffolding tool (package utility)
- guiNamingLinter: Naming convention checker (template + package utility)
- runLinter: Linter CLI interface (template + package utility)
- logUtils: Logging utility (package utility only)

Template files (copied to new projects):
- globalVars.py, baseFrame.py, frameTemplate.py, statusFrame.py
- mainMenu.py, styleUtils.py, guiNamingLinter.py, runLinter.py
- copilot-instructions.md
"""

__version__ = "0.1"

# Expose main functionality for programmatic use
from .createProject import createProject, updateProject
from .guiNamingLinter import lintFile, lintGuiNaming
from .runLinter import main as runLinter

__all__ = [
    'createProject',
    'updateProject',
    'lintFile',
    'lintGuiNaming',
    'runLinter',
]
