"""Tests for organiseMyProjects.agentCheck."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from organiseMyProjects.agentCheck import (
    AgentCheckValidator,
    Severity,
    checkProject,
    main,
)
from organiseMyProjects.manageProject import createProject
from organiseMyProjects.version import VERSION


@pytest.fixture
def validRepo(tmp_path: Path) -> Path:
    """Create a fully valid scaffolded project fixture."""
    repo = tmp_path / "myValidProject"
    createProject(repo, dryRun=False)

    reqFile = repo / "project" / "requirements" / "features" / "001-testFeature.md"
    reqFile.write_text(
        """# 001: Test feature

## Status

InProgress

## Outcome

As a user, I need testing so that code is validated.

## Context

Testing context.

## Scope

- Test scope.

## Out of scope

- None.

## Acceptance criteria

1. Given condition, when action, then result.

## Dependencies and decisions

- None.

## Verification

- pytest

## Traceability

- Implementation: pending
- Tests: pending
- Documentation: pending
- Pull request: pending
- Agent runs: None

## Change history

- 2026-08-16: created.
""",
        encoding="utf-8",
    )
    reqIndex = repo / "project" / "requirements" / "requirementsIndex.md"
    reqIndex.write_text(
        """# Requirements

Next available number: 002

## Requirement index

| Req ID | Requirement | Description | Status | Agent Prompt | Architecture Decisions |
| --- | --- | --- | --- | --- | --- |
| 001 | [Test feature](features/001-testFeature.md) | Test feature desc | InProgress | [Prompt](prompt/001-testFeature.md) | None |
""",
        encoding="utf-8",
    )

    promptFile = repo / "project" / "requirements" / "prompt" / "001-testFeature.md"
    promptFile.write_text("# 001 Prompt\n\nPrompt content\n", encoding="utf-8")

    incFile = repo / "project" / "currentIncrement.md"
    incFile.write_text(
        """# Current Development Increment

## Status

Active

## Objective

Deliver test feature.

## Governing References

- Primary Requirement: `project/requirements/features/001-testFeature.md`
- Supporting ADRs: None
- Milestone / Roadmap: `project/roadmap.md`

## Scope

- Test capability

## Explicit Exclusions

- None

## In-Progress Tasks

- [ ] Task 1

## Relevant Files & Components

- Implementation: `myValidProject/`
- Tests: `tests/`
- Documentation: `documentation/`

## Verification Procedures

```bash
pytest
```

## Definition of Done

1. Criteria pass.

## Handoff & Unresolved Context

- Next agent context.
""",
        encoding="utf-8",
    )

    addInst = repo / ".github" / "additional-instructions.md"
    addInst.write_text(
        """# Additional instructions

## Development checks

```bash
pytest
```
""",
        encoding="utf-8",
    )

    return repo


def testCheckProjectLogsOmpVersion(validRepo: Path):
    """The manageProject check path records the running OMP release."""
    with patch("organiseMyProjects.agentCheck.getLogger") as getLogger:
        assert checkProject(validRepo) == 0

    getLogger.return_value.value.assert_any_call("OMP version", VERSION)


class TestAgentCheckValidator:
    """Unit tests for the validator rule engine."""

    def testValidRepoPasses(self, validRepo: Path):
        report = AgentCheckValidator(validRepo).runAll()
        assert report.isSuccess
        assert len(report.failures) == 0

    def testMissingAgentsMdFails(self, validRepo: Path):
        (validRepo / "AGENTS.md").unlink()
        report = AgentCheckValidator(validRepo).runAll()
        assert not report.isSuccess
        assert any(f.ruleId == "ENT-001" for f in report.failures)

    def testAgentInstructionsMustRequireRequirementsGuide(self, validRepo: Path):
        instructions = validRepo / ".github" / "agent-instructions.md"
        content = instructions.read_text(encoding="utf-8")
        instructions.write_text(
            content.replace("Read `documentation/requirementsManagement.md`.\n", ""),
            encoding="utf-8",
        )

        report = AgentCheckValidator(validRepo).runAll()

        assert any(f.ruleId == "ENT-004" for f in report.failures)

    def testAgentInstructionsMustRequireRepositoryLayout(self, validRepo: Path):
        instructions = validRepo / ".github" / "agent-instructions.md"
        content = instructions.read_text(encoding="utf-8")
        instructions.write_text(
            content.replace(
                "Read `documentation/repositoryLayout.md` before adding or moving "
                "repository content.\n",
                "",
            ),
            encoding="utf-8",
        )

        report = AgentCheckValidator(validRepo).runAll()

        assert any(f.ruleId == "ENT-004" for f in report.failures)

    def testLegacyTestFilenameFails(self, validRepo: Path):
        legacyTest = validRepo / "tests" / "test_Foo.py"
        legacyTest.write_text("def test_example(): pass\n", encoding="utf-8")

        report = AgentCheckValidator(validRepo).runAll()

        assert any(f.ruleId == "TST-002" for f in report.failures)

    def testLegacyPromptInfixFails(self, validRepo: Path):
        reqIndex = validRepo / "project" / "requirements" / "requirementsIndex.md"
        content = reqIndex.read_text(encoding="utf-8")
        reqIndex.write_text(
            content.replace("001-testFeature.md", "001-testFeature.prompt.md"),
            encoding="utf-8",
        )

        report = AgentCheckValidator(validRepo).runAll()

        assert any(f.ruleId == "REQ-005" for f in report.failures)

    def testMissingReadmeFails(self, validRepo: Path):
        (validRepo / "README.md").unlink()
        report = AgentCheckValidator(validRepo).runAll()
        assert not report.isSuccess
        assert any(f.ruleId == "DOC-001" for f in report.failures)

    def testNestedReadmeFails(self, validRepo: Path):
        nestedReadme = validRepo / "documentation" / "topic" / "README.md"
        nestedReadme.parent.mkdir(parents=True)
        nestedReadme.write_text("# Topic\n", encoding="utf-8")

        report = AgentCheckValidator(validRepo).runAll()

        assert any(f.ruleId == "DOC-005" for f in report.failures)

    def testDeadMarkdownLinkFails(self, validRepo: Path):
        docFile = validRepo / "documentation" / "architecture.md"
        docFile.write_text(
            "# Architecture\n\nSee [non-existent](nonExistent.md)",
            encoding="utf-8",
        )
        report = AgentCheckValidator(validRepo).runAll()
        assert not report.isSuccess
        assert any(f.ruleId == "DOC-002" for f in report.failures)

    def testActiveIncrementReferencingMissingRequirementFails(self, validRepo: Path):
        incFile = validRepo / "project" / "currentIncrement.md"
        content = incFile.read_text(encoding="utf-8")
        incFile.write_text(
            content.replace("001-testFeature.md", "999-nonExistent.md"),
            encoding="utf-8",
        )
        report = AgentCheckValidator(validRepo).runAll()
        assert not report.isSuccess
        assert any(f.ruleId == "INC-002" for f in report.failures)

    def testActiveIncrementReferencingCompletedRequirementFails(self, validRepo: Path):
        reqFile = (
            validRepo / "project" / "requirements" / "features" / "001-testFeature.md"
        )
        content = reqFile.read_text(encoding="utf-8")
        reqFile.write_text(content.replace("InProgress", "Completed"), encoding="utf-8")

        reqIndex = validRepo / "project" / "requirements" / "requirementsIndex.md"
        indexContent = reqIndex.read_text(encoding="utf-8")
        reqIndex.write_text(
            indexContent.replace("InProgress", "Completed"), encoding="utf-8"
        )

        report = AgentCheckValidator(validRepo).runAll()
        assert not report.isSuccess
        assert any(f.ruleId == "INC-002" for f in report.failures)

    def testRequirementsStatusMismatchFails(self, validRepo: Path):
        reqIndex = validRepo / "project" / "requirements" / "requirementsIndex.md"
        indexContent = reqIndex.read_text(encoding="utf-8")
        reqIndex.write_text(
            indexContent.replace("InProgress", "ToDo"), encoding="utf-8"
        )

        report = AgentCheckValidator(validRepo).runAll()
        assert not report.isSuccess
        assert any(f.ruleId == "REQ-002" for f in report.failures)

    def testMissingAdrReferenceFails(self, validRepo: Path):
        reqFile = (
            validRepo / "project" / "requirements" / "features" / "001-testFeature.md"
        )
        content = reqFile.read_text(encoding="utf-8")
        reqFile.write_text(
            content.replace("None.", "Follow `project/adr/001-missingAdr.md`"),
            encoding="utf-8",
        )

        report = AgentCheckValidator(validRepo).runAll()
        assert not report.isSuccess
        assert any(f.ruleId == "REQ-003" for f in report.failures)

    def testPlaceholderDetectionWarning(self, validRepo: Path):
        incFile = validRepo / "project" / "currentIncrement.md"
        incFile.write_text(
            """# Current Development Increment

## Status

Active

<!-- Concise 1-2 sentence statement -->
- Deliverable behavior 1
""",
            encoding="utf-8",
        )
        report = AgentCheckValidator(validRepo).runAll()
        assert any(f.ruleId == "INC-004" for f in report.warnings)

    def testCliStrictExecution(self, validRepo: Path, monkeypatch):
        incFile = validRepo / "project" / "currentIncrement.md"
        incFile.write_text(
            """# Current Development Increment

## Status

Active

<!-- Concise 1-2 sentence statement -->
""",
            encoding="utf-8",
        )

        monkeypatch.setattr(sys, "argv", ["agentCheck", str(validRepo), "--strict"])
        assert main() == 1

        monkeypatch.setattr(sys, "argv", ["agentCheck", str(validRepo)])
        assert main() == 0


def testCheckCommandSeparatesHeaderAndSummary(validRepo, monkeypatch, capsys, caplog):
    import logging

    from organiseMyProjects import manageProject

    monkeypatch.setattr(Path, "home", lambda: validRepo)
    with caplog.at_level(logging.INFO):
        assert manageProject.main(["check", "--project", str(validRepo)]) == 0
    marker = "\n>" + "-" * 80 + "<\n\n"
    assert capsys.readouterr().out == marker + ("-" * 80 + "\n") * 2
    assert sum("OMP version" in record.getMessage() for record in caplog.records) == 1
    logFile = next((validRepo / ".local/state/manageProject").glob("*.log"))
    assert logFile.read_text().startswith(marker)
    assert logFile.read_text().count(marker) == 1
    lines = logFile.read_text().splitlines()
    header = next(i for i, text in enumerate(lines) if "checking project at" in text)
    summary = next(i for i, text in enumerate(lines) if "...failures:" in text)
    assert lines[header + 1] == "-" * 80
    assert lines[summary - 1] == "-" * 80


@pytest.mark.parametrize("nested", [False, True])
def testGitRootEntryPoints(validRepo, nested):
    import subprocess

    subprocess.run(["git", "init", str(validRepo)], check=True, capture_output=True)
    project = validRepo / "mailAgent" if nested else validRepo
    project.mkdir(exist_ok=True)
    validator = AgentCheckValidator(project)
    assert validator.repositoryRoot == validRepo.resolve()
    validator._checkEntryPoints()
    assert not [
        f
        for f in validator.report.findings
        if f.ruleId in {"ENT-001", "ENT-002", "ENT-003"}
    ]
    (validRepo / "AGENTS.md").unlink()
    validator = AgentCheckValidator(project)
    validator._checkEntryPoints()
    finding = next(f for f in validator.report.findings if f.ruleId == "ENT-001")
    assert finding.filePath == validRepo / "AGENTS.md"
    validator._checkManagedConventions()
    assert validator.rootPath == project.resolve()


def testNonGitRootFallback(tmp_path):
    validator = AgentCheckValidator(tmp_path)
    assert validator.repositoryRoot == tmp_path.resolve()


def testMissingGitRootFallback(tmp_path):
    with patch(
        "organiseMyProjects.agentCheck.subprocess.run", side_effect=FileNotFoundError
    ):
        validator = AgentCheckValidator(tmp_path)
    assert validator.repositoryRoot == tmp_path.resolve()


@pytest.mark.parametrize(
    ("relativePath", "rule"),
    [
        ("AGENTS.md", "ENT-001"),
        (".github/copilot-instructions.md", "ENT-002"),
        (".github/additional-instructions.md", "ENT-003"),
    ],
)
def testNestedMissingEntryPoints(validRepo, relativePath, rule):
    import subprocess

    subprocess.run(["git", "init", str(validRepo)], check=True, capture_output=True)
    project = validRepo / "mailAgent"
    project.mkdir()
    missing = validRepo / relativePath
    missing.unlink()
    validator = AgentCheckValidator(project)
    validator._checkEntryPoints()
    finding = next(f for f in validator.report.findings if f.ruleId == rule)
    assert finding.filePath == missing
    # Project tests remain local even if the repository has valid test settings.
    (project / "pytest.ini").write_text("[pytest]\npython_files = wrong.py\n")
    validator._checkManagedConventions()
    assert (
        next(f for f in validator.report.failures if f.ruleId == "TST-001").filePath
        == project / "pytest.ini"
    )


def testNestedProjectCheckProductionPath(validRepo, monkeypatch, caplog):
    import shutil
    import subprocess

    from organiseMyProjects import manageProjectCli

    subprocess.run(["git", "init", str(validRepo)], check=True, capture_output=True)
    project = validRepo / "mailAgent"
    shutil.copytree(
        validRepo, project, ignore=shutil.ignore_patterns(".git", "mailAgent")
    )
    shutil.rmtree(project / ".github")
    (project / "AGENTS.md").unlink()
    (project / "CLAUDE.md").unlink()
    readme = project / "README.md"
    readme.write_text(
        readme.read_text().replace(
            "](.github/agent-instructions.md)", "](../.github/agent-instructions.md)"
        )
    )
    monkeypatch.setattr(
        sys, "argv", ["manageProject", "check", "--project", str(project)]
    )
    assert manageProjectCli.main() == 0
    output = caplog.text
    assert "project root" in output
    assert "repository root" in output
    assert "[ENT-001]" not in output
    assert "[ENT-002]" not in output
    assert "[ENT-003]" not in output


def _ruleFindings(report, ruleId: str) -> list:
    return [finding for finding in report.findings if finding.ruleId == ruleId]


def _recordRename(repo: Path, newName: str, indexId: str | None = None) -> Path:
    """Rename the fixture record, keeping the index and prompt links aligned."""
    reqDir = repo / "project" / "requirements"
    newPath = reqDir / "features" / newName
    (reqDir / "features" / "001-testFeature.md").rename(newPath)
    (reqDir / "prompt" / "001-testFeature.md").rename(reqDir / "prompt" / newName)
    index = reqDir / "requirementsIndex.md"
    text = index.read_text(encoding="utf-8").replace("001-testFeature.md", newName)
    if indexId:
        text = text.replace("| 001 |", f"| {indexId} |")
    index.write_text(text, encoding="utf-8")
    return newPath


class TestRequirementConformance:
    """Requirement 015: records, index rows and prompts follow the guide."""

    def testConformingRepositoryHasNoConformanceFindings(self, validRepo: Path):
        report = AgentCheckValidator(validRepo).runAll()

        for ruleId in (
            "REQ-007",
            "REQ-008",
            "REQ-009",
            "REQ-010",
            "REQ-011",
            "REQ-012",
        ):
            assert _ruleFindings(report, ruleId) == []

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("001-test-feature.md", "001-testFeature.md"),
            ("MA-001-testFeature.md", "001-testFeature.md"),
            ("001-TestFeature.md", "001-testFeature.md"),
        ],
    )
    def testNonConformingFilenameFailsWithSuggestion(
        self, validRepo: Path, name: str, expected: str
    ):
        _recordRename(validRepo, name, "MA-001" if name.startswith("MA-") else None)

        report = AgentCheckValidator(validRepo).runAll()

        findings = _ruleFindings(report, "REQ-007")
        assert [f.severity for f in findings] == [Severity.FAILURE]
        assert f"'{expected}'" in findings[0].message

    @pytest.mark.parametrize(
        "heading",
        ["# REQ-001 - Test feature", "# MA-001 Test feature", "# 002: Test feature"],
    )
    def testNonConformingHeadingFails(self, validRepo: Path, heading: str):
        record = validRepo / "project/requirements/features/001-testFeature.md"
        text = record.read_text(encoding="utf-8")
        record.write_text(
            text.replace("# 001: Test feature", heading), encoding="utf-8"
        )

        report = AgentCheckValidator(validRepo).runAll()

        findings = _ruleFindings(report, "REQ-008")
        assert len(findings) == 1
        assert findings[0].severity == Severity.FAILURE
        assert "'# 001: Test feature'" in findings[0].message

    def testStatusLineWithoutSectionFails(self, validRepo: Path):
        record = validRepo / "project/requirements/features/001-testFeature.md"
        text = record.read_text(encoding="utf-8")
        record.write_text(
            text.replace("## Status\n\nInProgress", "Status: InProgress"),
            encoding="utf-8",
        )

        report = AgentCheckValidator(validRepo).runAll()

        failures = [
            f
            for f in _ruleFindings(report, "REQ-009")
            if f.severity == Severity.FAILURE
        ]
        assert len(failures) == 1
        assert "## Status" in failures[0].message

    def testOtherMissingSectionsOnlyWarn(self, validRepo: Path):
        record = validRepo / "project/requirements/features/001-testFeature.md"
        text = record.read_text(encoding="utf-8")
        text = text.replace("## Context\n\nTesting context.\n\n", "")
        record.write_text(
            text.replace("## Acceptance criteria", "## Acceptance Criteria"),
            encoding="utf-8",
        )

        report = AgentCheckValidator(validRepo).runAll()

        findings = _ruleFindings(report, "REQ-009")
        assert [f.severity for f in findings] == [Severity.WARNING]
        assert findings[0].message.endswith("Context")
        assert report.isSuccess

    def testPrefixedIndexIdFailsInsteadOfBeingSkipped(self, validRepo: Path):
        index = validRepo / "project/requirements/requirementsIndex.md"
        text = index.read_text(encoding="utf-8")
        index.write_text(text.replace("| 001 |", "| MA-001 |"), encoding="utf-8")

        report = AgentCheckValidator(validRepo).runAll()

        findings = _ruleFindings(report, "REQ-010")
        assert len(findings) == 1
        assert "'MA-001' should be '001'" in findings[0].message
        assert findings[0].line is not None

    def testPromptOutsideCanonicalDirectoryFails(self, validRepo: Path):
        reqDir = validRepo / "project" / "requirements"
        legacy = validRepo / "project" / "prompts"
        legacy.mkdir()
        (reqDir / "prompt" / "001-testFeature.md").rename(legacy / "001-testFeature.md")
        index = reqDir / "requirementsIndex.md"
        text = index.read_text(encoding="utf-8")
        index.write_text(
            text.replace(
                "](prompt/001-testFeature.md)", "](../prompts/001-testFeature.md)"
            ),
            encoding="utf-8",
        )

        report = AgentCheckValidator(validRepo).runAll()

        messages = [f.message for f in _ruleFindings(report, "REQ-011")]
        assert len(messages) == 2
        assert any("../prompts/001-testFeature.md" in message for message in messages)
        assert any(
            "project/requirements/prompt/001-testFeature.md" in message
            for message in messages
        )

    def testIndexDeclaringPrefixWarns(self, validRepo: Path):
        index = validRepo / "project/requirements/requirementsIndex.md"
        text = index.read_text(encoding="utf-8")
        index.write_text(
            text.replace(
                "# Requirements\n",
                "# Requirements\n\nNew requirement records use the stable project prefix `MA`.\n",
            ),
            encoding="utf-8",
        )

        report = AgentCheckValidator(validRepo).runAll()

        findings = _ruleFindings(report, "REQ-012")
        assert [f.severity for f in findings] == [Severity.WARNING]
