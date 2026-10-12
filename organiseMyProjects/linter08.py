"""OMP 0.8 linter compatibility rules.

The 0.8 release keeps the established linter implementation intact while
installing narrowly scoped behaviour for approved product names, digit-bearing
domainAction names, and framework-mandated Textual method names.
"""

from __future__ import annotations

import re
from typing import Callable

LOGGING_CASE_WHITELIST = frozenset(
    {
        "DJI",
        "Firefox",
        "GoPro",
        "Grok",
        "MCM",
        "SQLite",
        "TVDB",
        "X.ai",
    }
)

TEXTUAL_METHOD_PATTERNS = (
    re.compile(r"^action_[a-z][a-z0-9_]*$"),
    re.compile(r"^on_[a-z][a-z0-9_]*$"),
)

DOMAIN_ACTION_PATTERN = r"^_?[a-z][a-z0-9]*[A-Z][a-zA-Z0-9]*$"
_LOGGING_CASE_RULES = {"Logging (info)", "Logging (warning)", "Logging (error)"}


def _frameworkDetect(original: Callable, fileContent: str) -> str | None:
    """Recognise Textual imports without changing Tkinter or Qt detection."""
    if re.search(
        r"(?m)^\s*(?:from\s+textual(?:\.|\s)|import\s+textual\b)", fileContent
    ):
        return "textual"
    return original(fileContent)


def _textualMethodName(name: str) -> bool:
    return any(pattern.fullmatch(name) for pattern in TEXTUAL_METHOD_PATTERNS)


def _whitelistNormalise(message: str) -> str:
    """Lower approved case-sensitive tokens for casing validation only."""
    normalised = message
    for token in sorted(LOGGING_CASE_WHITELIST, key=len, reverse=True):
        pattern = rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])"
        normalised = re.sub(pattern, token.casefold(), normalised)
    return normalised


def _loggingCaseValid(message: str, ruleType: str) -> bool:
    normalised = _whitelistNormalise(message)
    if ruleType in {"Logging (info)", "Logging (warning)"}:
        return normalised.islower()
    if ruleType == "Logging (error)":
        return normalised == normalised.capitalize()
    return False


def guiNamingPatchesInstall(guiNamingModule) -> None:
    """Install requirement 007 behaviour into guiNamingLinter."""
    visitor = guiNamingModule.GuiNamingVisitor
    if getattr(visitor, "_requirement007Patched", False):
        return

    guiNamingModule.DOMAIN_ACTION_PATTERN = DOMAIN_ACTION_PATTERN

    originalFrameworkDetect: Callable = guiNamingModule.frameworkDetect

    def frameworkDetect(fileContent: str) -> str | None:
        return _frameworkDetect(originalFrameworkDetect, fileContent)

    guiNamingModule.frameworkDetect = frameworkDetect

    originalNamingExempt: Callable = visitor.functionIsNamingExempt

    def functionIsNamingExempt(self, node) -> bool:
        if self.framework == "textual" and _textualMethodName(node.name):
            return True
        return originalNamingExempt(self, node)

    visitor.functionIsNamingExempt = functionIsNamingExempt

    originalLoggingCheck: Callable = visitor.loggingCheckExpression

    def loggingCheckExpression(self, node) -> None:
        before = len(self.violations)
        originalLoggingCheck(self, node)
        if len(self.violations) == before:
            return
        prefix = self.violations[:before]
        added = [
            finding
            for finding in self.violations[before:]
            if not (
                finding[1] in _LOGGING_CASE_RULES
                and _loggingCaseValid(finding[0], finding[1])
            )
        ]
        self.violations[:] = [*prefix, *added]

    visitor.loggingCheckExpression = loggingCheckExpression

    originalSpellingCheck: Callable = visitor.spellingCheckExpression

    def spellingCheckExpression(self, node) -> None:
        parent = getattr(node, "parent", None)
        parentBody = getattr(parent, "body", None)
        isDocstring = (
            isinstance(
                parent,
                (
                    guiNamingModule.ast.Module,
                    guiNamingModule.ast.ClassDef,
                    guiNamingModule.ast.FunctionDef,
                    guiNamingModule.ast.AsyncFunctionDef,
                ),
            )
            and bool(parentBody)
            and parentBody[0] is node
        )
        if isDocstring:
            return
        originalSpellingCheck(self, node)

    visitor.spellingCheckExpression = spellingCheckExpression
    visitor._requirement007Patched = True


def runLinterPatchesInstall(runLinterModule) -> None:
    """Remove the broad 0.7 case overlay now that 0.8 validates exact tokens."""
    if getattr(runLinterModule, "_requirement007Patched", False):
        return

    originalViolationAllowed: Callable = runLinterModule._violationAllowed

    def _violationAllowed(name: str, ruleType: str) -> bool:
        if ruleType in _LOGGING_CASE_RULES:
            return name in runLinterModule.LOGGING_MESSAGE_ALLOWLIST
        return originalViolationAllowed(name, ruleType)

    runLinterModule._violationAllowed = _violationAllowed
    runLinterModule._requirement007Patched = True
