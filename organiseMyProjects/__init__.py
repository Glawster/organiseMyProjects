"""organiseMyProjects - Python project scaffolding toolkit.

This package provides tools to create and manage Python projects with:
- Predefined project structure
- GUI framework components
- Naming convention linters
- Development guidelines
- Logging utilities

Main components:
- createProject: Project scaffolding tool (package utility)
- guiNamingLinter: Naming convention checker (template + package utility)
- runLinter: Linter CLI interface (template + package utility)
- logUtils: Logging utility (package utility only)

Template files (copied to new projects):
- globalVars.py, baseFrame.py, frameTemplate.py, statusFrame.py
- mainMenu.py, styleUtils.py, guiNamingLinter.py, runLinter.py
- .github/copilot-instructions.md (copied from this repo's .github/)

Usage:
    from organiseMyProjects import createProject, runLinter
    from organiseMyProjects.logUtils import getLogger, thisApplication
"""

__version__ = "0.2"

# Expose main functionality for programmatic use
from . import createProject
from .guiNamingLinter import lintFile, lintGuiNaming
from . import runLinter
from . import logUtils

__all__ = [
    'createProject',
    'lintFile',
    'lintGuiNaming',
    'runLinter',
    'logUtils',
]
