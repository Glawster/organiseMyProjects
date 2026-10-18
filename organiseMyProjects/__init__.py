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

Template files (copied to new projects):
- globalVars.py, baseFrame.py, frameTemplate.py, statusFrame.py
- mainMenu.py, styleUtils.py
- .github/agent-instructions.md (copied from this repo's .github/)

Usage:
    from organiseMyProjects import manageProject, runLinter
    from organiseMyProjects.logUtils import getLogger, setApplication
"""

# Expose main functionality for programmatic use
from . import agentCheck, guiNamingLinter, logUtils, manageProject, runLinter
from .guiNamingLinter import lintFile, lintGuiNaming
from .version import VERSION as __version__

__all__ = [
    "__version__",
    "agentCheck",
    "guiNamingLinter",
    "lintFile",
    "lintGuiNaming",
    "logUtils",
    "manageProject",
    "runLinter",
]
