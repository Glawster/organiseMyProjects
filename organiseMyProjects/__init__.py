"""organiseMyProjects - Python project scaffolding toolkit.

This package provides tools to create and manage Python projects with:
- Predefined project structure
- GUI framework components
- Naming convention linters
- Development guidelines
- Logging utilities

Main components:
- manageProject: Project scaffolding tool (package utility)
- guiNamingLinter: Naming convention checker (package utility)
- runLinter: Linter CLI interface (template + package utility)
- logUtils: Logging utility (package utility only)

Template files (copied to new projects):
- globalVars.py, baseFrame.py, frameTemplate.py, statusFrame.py
- mainMenu.py, styleUtils.py, runLinter.py
- .github/agent-instructions.md (copied from this repo's .github/)

Usage:
    from organiseMyProjects import manageProject, runLinter
    from organiseMyProjects.logUtils import getLogger, thisApplication
"""

from .version import VERSION as __version__

# Expose main functionality for programmatic use
from . import manageProject
from .guiNamingLinter import lintFile, lintGuiNaming
from . import runLinter
from . import logUtils

__all__ = [
    "manageProject",
    "lintFile",
    "lintGuiNaming",
    "runLinter",
    "logUtils",
]
