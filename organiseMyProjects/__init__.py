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

# Expose main functionality for programmatic use
from . import agentCheck, logUtils, manageProject, runLinter
from .guiNamingLinter import lintFile, lintGuiNaming
from .version import VERSION as __version__

__all__ = [
    "__version__",
    "agentCheck",
    "lintFile",
    "lintGuiNaming",
    "logUtils",
    "manageProject",
    "runLinter",
]
