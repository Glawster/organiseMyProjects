"""organiseMyProjects.agentCheck

Deterministic static validator for AI agent readiness, repository consistency,
and relational integrity across OMP-managed projects.
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from organiseMyProjects.logUtils import getLogger, setApplication
from organiseMyProjects.version import VERSION


class Severity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    FAILURE = "FAILURE"


@dataclass
class Finding:
    ruleId: str
    severity: Severity
    message: str
    filePath: Optional[Path] = None
    line: Optional[int] = None


@dataclass
class CheckReport:
    findings: list[Finding] = field(default_factory=list)

    def findingAdd(
        self,
        ruleId: str,
        severity: Severity,
        message: str,
        filePath: Optional[Path] = None,
        line: Optional[int] = None,
    ) -> None:
        self.findings.append(Finding(ruleId, severity, message, filePath, line))

    # Compatibility alias for existing callers; the implementation follows the
    # project domainAction naming convention.
    add = findingAdd

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.FAILURE]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.WARNING]

    @property
    def isSuccess(self) -> bool:
        return len(self.failures) == 0


class AgentCheckValidator:
    """Evaluates repository files against agent-readiness and consistency rules."""

    def __init__(self, rootPath: Path, verbose: bool = False):
        self.rootPath = rootPath.resolve()
        self.verbose = verbose
        self.report = CheckReport()

    def runAll(self) -> CheckReport:
        """Run all validation rule families."""
        self._checkEntryPoints()
        self._checkManagedConventions()
        self._checkDocumentation()
        self._checkCurrentIncrement()
        self._checkRequirementsAndAdrs()
        return self.report

    # -----------------------------------------------------------------------
    # Rule Family: ENT (Agent Entry Points)
    # -----------------------------------------------------------------------

    def _checkEntryPoints(self) -> None:
        # ENT-001: AGENTS.md must exist and link to agent-instructions.md
        agentsMd = self.rootPath / "AGENTS.md"
        if not agentsMd.exists():
            self.report.add(
                "ENT-001",
                Severity.FAILURE,
                "AGENTS.md is missing from the repository root",
                agentsMd,
            )
        else:
            try:
                content = agentsMd.read_text(encoding="utf-8")
                if "agent-instructions.md" not in content:
                    self.report.add(
                        "ENT-001",
                        Severity.FAILURE,
                        "AGENTS.md does not reference .github/agent-instructions.md",
                        agentsMd,
                    )
            except OSError as exc:
                self.report.add(
                    "ENT-001",
                    Severity.FAILURE,
                    f"Could not read AGENTS.md: {exc}",
                    agentsMd,
                )

        # ENT-002: Vendor shims should exist and point directly to agent-instructions.md
        copilotShim = self.rootPath / ".github" / "copilot-instructions.md"
        if copilotShim.exists():
            try:
                cContent = copilotShim.read_text(encoding="utf-8")
                if "agent-instructions.md" not in cContent:
                    self.report.add(
                        "ENT-002",
                        Severity.WARNING,
                        ".github/copilot-instructions.md does not reference .github/agent-instructions.md",
                        copilotShim,
                    )
            except OSError:
                pass
        else:
            self.report.add(
                "ENT-002",
                Severity.WARNING,
                ".github/copilot-instructions.md is missing",
                copilotShim,
            )

        claudeShim = self.rootPath / "CLAUDE.md"
        if claudeShim.exists():
            try:
                clContent = claudeShim.read_text(encoding="utf-8")
                if "agent-instructions.md" not in clContent:
                    self.report.add(
                        "ENT-002",
                        Severity.WARNING,
                        "CLAUDE.md does not reference .github/agent-instructions.md",
                        claudeShim,
                    )
            except OSError:
                pass

        # ENT-003: .github/additional-instructions.md should exist
        addInstructions = self.rootPath / ".github" / "additional-instructions.md"
        if not addInstructions.exists():
            self.report.add(
                "ENT-003",
                Severity.WARNING,
                ".github/additional-instructions.md is missing",
                addInstructions,
            )

        # ENT-004: requirements guidance is mandatory context for agents.
        agentInstructions = self.rootPath / ".github" / "agent-instructions.md"
        if agentInstructions.exists():
            try:
                instructionsText = agentInstructions.read_text(encoding="utf-8")
                requiredText = "Read `documentation/requirementsManagement.md`."
                if requiredText not in instructionsText:
                    self.report.add(
                        "ENT-004",
                        Severity.FAILURE,
                        f".github/agent-instructions.md must contain: {requiredText}",
                        agentInstructions,
                    )
                layoutText = (
                    "Read `documentation/repositoryLayout.md` before adding or moving "
                    "repository content."
                )
                if layoutText not in instructionsText:
                    self.report.add(
                        "ENT-004",
                        Severity.FAILURE,
                        f".github/agent-instructions.md must contain: {layoutText}",
                        agentInstructions,
                    )
            except OSError:
                pass

    def _checkManagedConventions(self) -> None:
        """Validate OMP-managed pytest and test-module naming conventions."""
        pytestIni = self.rootPath / "pytest.ini"
        if pytestIni.exists():
            try:
                if "python_files = test_[a-z]*.py" not in pytestIni.read_text(
                    encoding="utf-8"
                ):
                    self.report.add(
                        "TST-001",
                        Severity.FAILURE,
                        "pytest.ini must use python_files = test_[a-z]*.py",
                        pytestIni,
                    )
            except OSError:
                pass

        testsPath = self.rootPath / "tests"
        if testsPath.is_dir():
            for testFile in sorted(testsPath.glob("test_*.py")):
                if re.fullmatch(r"test_[a-z][A-Za-z0-9]*\.py", testFile.name) is None:
                    self.report.add(
                        "TST-002",
                        Severity.FAILURE,
                        "Python test filename must follow test_camelCaseName.py",
                        testFile,
                    )

    # -----------------------------------------------------------------------
    # Rule Family: DOC (Living Documentation & Index Integrity)
    # -----------------------------------------------------------------------

    def _checkDocumentation(self) -> None:
        readme = self.rootPath / "README.md"
        if not readme.exists():
            self.report.add(
                "DOC-001",
                Severity.FAILURE,
                "README.md is missing from the repository root",
                readme,
            )
            return

        try:
            readme.read_text(encoding="utf-8")
        except OSError as exc:
            self.report.add(
                "DOC-001",
                Severity.FAILURE,
                f"Could not read README.md: {exc}",
                readme,
            )
            return

        # Check single H1 rule and relative link validity across markdown files
        for mdFile in self.rootPath.glob("**/*.md"):
            # Skip virtualenvs or cache directories
            if any(
                p in mdFile.parts
                for p in (".git", ".pytest_cache", "__pycache__", "build", "output")
            ):
                continue
            self._validateMarkdownFile(mdFile)

        # Check build/verification commands discoverability
        addInstructions = self.rootPath / ".github" / "additional-instructions.md"
        devDocs = [readme]
        if addInstructions.exists():
            devDocs.append(addInstructions)
        devGuide = self.rootPath / "documentation" / "developer.md"
        if devGuide.exists():
            devDocs.append(devGuide)

        hasTestCommand = False
        for f in devDocs:
            try:
                txt = f.read_text(encoding="utf-8")
                if any(
                    cmd in txt
                    for cmd in ("pytest", "python -m unittest", "pytest tests")
                ):
                    hasTestCommand = True
                    break
            except OSError:
                pass

        if not hasTestCommand:
            self.report.add(
                "DOC-003",
                Severity.WARNING,
                "No discoverable test command (e.g. `pytest`) found in README.md, developer.md, or additional-instructions.md",
            )

    def _validateMarkdownFile(self, mdPath: Path) -> None:
        try:
            content = mdPath.read_text(encoding="utf-8")
        except OSError:
            return

        # Strip code blocks for heading and link extraction so example syntax is not checked
        textWithoutCode = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        textWithoutCode = re.sub(r"````.*?````", "", textWithoutCode, flags=re.DOTALL)

        lines = textWithoutCode.splitlines()
        h1Count = sum(
            1
            for line in lines
            if line.strip().startswith("# ") and not line.strip().startswith("<!--")
        )
        if h1Count > 1:
            self.report.add(
                "DOC-004",
                Severity.WARNING,
                f"Markdown file contains {h1Count} H1 ('# ') headings (expected exactly 1)",
                mdPath,
            )

        # Extract internal markdown links [label](path) outside code blocks
        linkMatches = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", textWithoutCode)
        for _, linkTarget in linkMatches:
            linkTarget = linkTarget.strip()
            # Ignore external links, mailto, conversation links, or anchors alone
            if (
                linkTarget.startswith(("http://", "https://", "mailto:", "#"))
                or "conversation://" in linkTarget
            ):
                continue

            # Strip query params or local anchor
            targetFilePart = linkTarget.split("#")[0].split("?")[0]
            if not targetFilePart:
                continue

            resolvedTarget = (mdPath.parent / targetFilePart).resolve()
            if not resolvedTarget.exists():
                self.report.add(
                    "DOC-002",
                    Severity.FAILURE,
                    f"Dead internal markdown link '{linkTarget}' does not resolve to an existing file",
                    mdPath,
                )

    # -----------------------------------------------------------------------
    # Rule Family: INC (Current Development Increment)
    # -----------------------------------------------------------------------

    def _checkCurrentIncrement(self) -> None:
        incFile = self.rootPath / "project" / "currentIncrement.md"
        if not incFile.exists():
            self.report.add(
                "INC-001",
                Severity.WARNING,
                "project/currentIncrement.md does not exist",
                incFile,
            )
            return

        try:
            content = incFile.read_text(encoding="utf-8")
        except OSError as exc:
            self.report.add(
                "INC-001",
                Severity.FAILURE,
                f"Could not read project/currentIncrement.md: {exc}",
                incFile,
            )
            return

        # Check for placeholder markers
        placeholders = [
            "<!-- Concise 1-2 sentence",
            "Deliverable behavior 1",
            "Deliverable behavior 2",
            "<!-- Key user or system",
            "Initial task",
        ]
        foundPlaceholders = [p for p in placeholders if p in content]
        if foundPlaceholders:
            self.report.add(
                "INC-004",
                Severity.WARNING,
                f"project/currentIncrement.md contains unedited template placeholder(s): {', '.join(foundPlaceholders)}",
                incFile,
            )

        # Check status
        statusMatch = re.search(r"## Status\s*\n+([A-Za-z]+)", content)
        status = statusMatch.group(1).strip() if statusMatch else ""

        # If active, check referenced requirement
        if status.lower() == "active":
            reqMatches = re.findall(
                r"project/requirements/features/(\d{3}-[A-Za-z0-9_-]+\.md)", content
            )
            for reqName in reqMatches:
                reqPath = (
                    self.rootPath / "project" / "requirements" / "features" / reqName
                )
                if not reqPath.exists():
                    self.report.add(
                        "INC-002",
                        Severity.FAILURE,
                        f"Active increment references non-existent requirement: project/requirements/features/{reqName}",
                        incFile,
                    )
                else:
                    # Check that the requirement is not marked Completed
                    try:
                        reqContent = reqPath.read_text(encoding="utf-8")
                        reqStatusMatch = re.search(
                            r"## Status\s*\n+([A-Za-z]+)", reqContent
                        )
                        if (
                            reqStatusMatch
                            and reqStatusMatch.group(1).strip().lower() == "completed"
                        ):
                            self.report.add(
                                "INC-002",
                                Severity.FAILURE,
                                f"Active increment references requirement '{reqName}' which is already marked Completed",
                                incFile,
                            )
                    except OSError:
                        pass

            # Check relevant files
            relevantFilesSection = re.search(
                r"## Relevant Files & Components(.*?)(?=## |\Z)",
                content,
                re.DOTALL,
            )
            if relevantFilesSection:
                sectionText = relevantFilesSection.group(1)
                # Find backtick paths
                explicitPaths = re.findall(r"`([A-Za-z0-9_./\-]+)`", sectionText)
                for relPath in explicitPaths:
                    # Skip directories or generic patterns like src/ or tests/
                    if relPath.endswith("/") or "*" in relPath:
                        continue
                    resolvedFile = (self.rootPath / relPath).resolve()
                    if not resolvedFile.exists():
                        self.report.add(
                            "INC-003",
                            Severity.WARNING,
                            f"Relevant file '{relPath}' referenced in currentIncrement.md does not exist on disk",
                            incFile,
                        )

    # -----------------------------------------------------------------------
    # Rule Family: REQ (Requirements & ADR Traceability)
    # -----------------------------------------------------------------------

    def _checkRequirementsAndAdrs(self) -> None:
        reqDir = self.rootPath / "project" / "requirements"
        featuresDir = reqDir / "features"
        reqReadme = reqDir / "README.md"

        if not featuresDir.exists() or not featuresDir.is_dir():
            return

        featureFiles = {f.name: f for f in featuresDir.glob("*.md")}
        promptsDir = reqDir / "prompt"

        if reqReadme.exists():
            try:
                readmeContent = reqReadme.read_text(encoding="utf-8")
                # REQ-001: Every feature file should be mentioned in requirements README
                for featName, featPath in featureFiles.items():
                    if featName not in readmeContent:
                        self.report.add(
                            "REQ-001",
                            Severity.FAILURE,
                            f"Requirement '{featName}' is not listed in project/requirements/README.md index",
                            featPath,
                        )

                # REQ-005: a single prompt has exactly the requirement filename;
                # letter suffixes are reserved for genuinely distinct prompts.
                promptLinks = re.findall(r"\]\(prompt/([^)]+\.md)\)", readmeContent)
                for promptName in promptLinks:
                    if ".prompt.md" in promptName:
                        self.report.add(
                            "REQ-005",
                            Severity.FAILURE,
                            f"Prompt '{promptName}' uses the obsolete .prompt infix",
                            reqReadme,
                        )
                    baseName = re.sub(r"^(\d{3})[a-z]-", r"\1-", promptName)
                    if baseName not in featureFiles:
                        self.report.add(
                            "REQ-005",
                            Severity.FAILURE,
                            f"Prompt '{promptName}' has no deterministic requirement filename match",
                            reqReadme,
                        )
                    if promptsDir.is_dir() and not (promptsDir / promptName).exists():
                        self.report.add(
                            "REQ-005",
                            Severity.FAILURE,
                            f"Prompt '{promptName}' linked from the index does not exist",
                            reqReadme,
                        )

                # REQ-002: Status consistency
                for featName, featPath in featureFiles.items():
                    try:
                        featText = featPath.read_text(encoding="utf-8")
                        featStatusMatch = re.search(
                            r"## Status\s*\n+([A-Za-z]+)", featText
                        )
                        featStatus = (
                            featStatusMatch.group(1).strip() if featStatusMatch else ""
                        )

                        # Look for row in README table
                        tableRowMatch = re.search(
                            rf"\|\s*\d+\s*\|\s*\[.*?\]\(features/{re.escape(featName)}\)\s*\|\s*.*?\s*\|\s*([A-Za-z]+)\s*\|",
                            readmeContent,
                        )
                        if tableRowMatch:
                            tableStatus = tableRowMatch.group(1).strip()
                            if (
                                featStatus
                                and tableStatus
                                and featStatus.casefold() != tableStatus.casefold()
                            ):
                                self.report.add(
                                    "REQ-002",
                                    Severity.FAILURE,
                                    f"Status mismatch for {featName}: README index states '{tableStatus}' but record states '{featStatus}'",
                                    featPath,
                                )

                    except OSError:
                        pass
            except OSError:
                pass

        # ADR Reference Check
        adrDir = self.rootPath / "project" / "adr"
        if adrDir.exists() and adrDir.is_dir():
            for featPath in featureFiles.values():
                try:
                    featText = featPath.read_text(encoding="utf-8")
                    adrMatches = re.findall(
                        r"project/adr/(\d{3}-[A-Za-z0-9_-]+\.md)", featText
                    )
                    for adrName in adrMatches:
                        if not (adrDir / adrName).exists():
                            self.report.add(
                                "REQ-003",
                                Severity.FAILURE,
                                f"Requirement '{featPath.name}' references non-existent ADR 'project/adr/{adrName}'",
                                featPath,
                            )
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate repository AI agent-readiness and context integrity."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root path to validate (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: treat warnings as failures (non-zero exit code)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed evaluation output",
    )
    return parser


def checkProject(
    targetPath: Optional[Path] = None,
    strict: bool = False,
    verbose: bool = False,
) -> int:
    """Validate a project for AI agent-readiness and context integrity.

    Returns 0 on success, non-zero on failure.
    """
    resolvedPath = (targetPath or Path.cwd()).resolve()
    thisApplication = "manageProject"
    setApplication(thisApplication)
    logger = getLogger(includeConsole=True)

    logger.value("OMP version", VERSION)
    logger.doing(f"checking project at {resolvedPath}")
    validator = AgentCheckValidator(resolvedPath, verbose=verbose)
    report = validator.runAll()

    failureCount = len(report.failures)
    warningCount = len(report.warnings)

    for finding in report.findings:
        location = (
            f" ({finding.filePath.relative_to(resolvedPath)})"
            if finding.filePath and finding.filePath.is_relative_to(resolvedPath)
            else (f" ({finding.filePath})" if finding.filePath else "")
        )
        msg = f"[{finding.ruleId}] {finding.message}{location}"
        if finding.severity == Severity.FAILURE:
            logger.error(msg)
        elif finding.severity == Severity.WARNING:
            logger.warning(msg)
        elif verbose:
            logger.info(msg)

    logger.value("failures", failureCount)
    logger.value("warnings", warningCount)

    isFailure = failureCount > 0 or (strict and warningCount > 0)
    if isFailure:
        logger.done("check failed")
        return 1

    logger.done("check passed")
    return 0


def main() -> int:
    parser = buildParser()
    args = parser.parse_args()
    return checkProject(Path(args.path), strict=args.strict, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
