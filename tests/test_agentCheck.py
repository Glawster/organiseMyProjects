"""Tests for organiseMyProjects.agentCheck."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from organiseMyProjects.agentCheck import (
    AgentCheckValidator,
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
    reqIndex = repo / "project" / "requirements" / "folderIndex.md"
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
        reqIndex = validRepo / "project" / "requirements" / "folderIndex.md"
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

        reqIndex = validRepo / "project" / "requirements" / "folderIndex.md"
        indexContent = reqIndex.read_text(encoding="utf-8")
        reqIndex.write_text(
            indexContent.replace("InProgress", "Completed"), encoding="utf-8"
        )

        report = AgentCheckValidator(validRepo).runAll()
        assert not report.isSuccess
        assert any(f.ruleId == "INC-002" for f in report.failures)

    def testRequirementsStatusMismatchFails(self, validRepo: Path):
        reqIndex = validRepo / "project" / "requirements" / "folderIndex.md"
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
