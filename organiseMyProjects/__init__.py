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
- runLinter: Linter CLI interface (package utility)
- logUtils: Logging utility (package utility)
- myBoard: Requirement board for the project the command is run from

Template files (copied to new projects):
- globalVars.py, baseFrame.py, frameTemplate.py, statusFrame.py
- mainMenu.py, styleUtils.py
- .github/agent-instructions.md (copied from this repo's .github/)

Usage:
    from organiseMyProjects import manageProject, runLinter
    from organiseMyProjects.logUtils import getLogger, setApplication
"""

# Expose main functionality for programmatic use
from . import (
    agentCheck,
    guiNamingLinter,
    logUtils,
    manageProject,
    requirementBoard,
    runLinter,
)
from .guiNamingLinter import lintFile, lintGuiNaming
from .requirementBoard import boardLoad, cardMove, requirementCreate
from .version import VERSION as __version__

__all__ = [
    "__version__",
    "agentCheck",
    "boardLoad",
    "cardMove",
    "guiNamingLinter",
    "lintFile",
    "lintGuiNaming",
    "logUtils",
    "manageProject",
    "requirementBoard",
    "requirementCreate",
    "runLinter",
]
