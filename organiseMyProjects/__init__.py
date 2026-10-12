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
from .linter08 import guiNamingPatchesInstall, runLinterPatchesInstall
from .linterCentralisation import manageProjectLinterPatchesInstall
from .requirementLayout import agentCheckPatchesInstall, manageProjectPatchesInstall
from .requirementsPromptIndex import promptIndexPatchesInstall
from .version import VERSION as __version__

# OMP 0.6 requirement 004 changes directory-index and requirement/prompt layout
# while preserving the established project-management implementation. Install
# the compatibility hooks once at package import so CLI and programmatic callers
# receive the same deterministic migration behaviour.
manageProjectPatchesInstall(manageProject)
agentCheckPatchesInstall(agentCheck)
promptIndexPatchesInstall(manageProject, agentCheck)

# OMP 0.8 keeps the installed package as the linter source of truth, removes
# recognised obsolete downstream copies, and applies exact framework/casing
# exemptions without weakening the core naming rules.
guiNamingPatchesInstall(guiNamingLinter)
runLinterPatchesInstall(runLinter)
manageProjectLinterPatchesInstall(manageProject)

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
