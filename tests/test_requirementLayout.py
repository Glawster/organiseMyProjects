from pathlib import Path

import pytest

from organiseMyProjects.requirementLayout import (
    layoutMigrate,
    requirementFilenameSuggest,
)


class _Logger:
    def __init__(self):
        self.actions = []
        self.infoMessages = []

    def action(self, message):
        self.actions.append(message)

    def info(self, message):
        self.infoMessages.append(message)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def testIndexReadmeMigratesToRequirementsIndex(tmp_path):
    source = tmp_path / "project/requirements/README.md"
    destination = tmp_path / "project/requirements/requirementsIndex.md"
    _write(
        source,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )

    layoutMigrate(tmp_path)

    assert not source.exists()
    assert destination.exists()


def testHistoricalRequirementsReadmeMigrates(tmp_path):
    source = tmp_path / "project/requirements/README.md"
    destination = tmp_path / "project/requirements/requirementsIndex.md"
    _write(
        source,
        "# Requirements\n\n"
        "Next available number: 019\n\n"
        "## ToDo\n\n"
        "- [001 — Handbook foundation](features/001-handbookFoundation.md)\n",
    )

    layoutMigrate(tmp_path)

    assert not source.exists()
    assert destination.exists()


def testHistoricalAdrReadmeMigrates(tmp_path):
    source = tmp_path / "project/adr/README.md"
    destination = tmp_path / "project/adr/adrIndex.md"
    _write(
        source,
        "# Architecture decision records\n\n"
        "## Records\n\n"
        "- [001: Handbook before software](001-handbookBeforeSoftware.md)\n",
    )

    layoutMigrate(tmp_path)

    assert not source.exists()
    assert destination.exists()


def testMistakenFolderIndexesMigrateToNamedIndexes(tmp_path):
    reqSource = tmp_path / "project/requirements/folderIndex.md"
    adrSource = tmp_path / "project/adr/folderIndex.md"
    _write(
        reqSource,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )
    _write(
        adrSource,
        "# Architecture Decision Records\n\nNext available number: 002\n\n## Decision index\n",
    )

    layoutMigrate(tmp_path)

    assert not reqSource.exists()
    assert not adrSource.exists()
    assert (tmp_path / "project/requirements/requirementsIndex.md").exists()
    assert (tmp_path / "project/adr/adrIndex.md").exists()


def testCanonicalNamedIndexesArePreserved(tmp_path):
    reqIndex = tmp_path / "project/requirements/requirementsIndex.md"
    adrIndex = tmp_path / "project/adr/adrIndex.md"
    _write(
        reqIndex,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )
    _write(
        adrIndex,
        "# Architecture Decision Records\n\nNext available number: 002\n\n## Decision index\n",
    )

    layoutMigrate(tmp_path)

    assert reqIndex.exists()
    assert adrIndex.exists()


def testIndexMigrationDryRunDoesNotChangeFiles(tmp_path):
    source = tmp_path / "project/requirements/README.md"
    _write(
        source,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )
    logger = _Logger()

    layoutMigrate(tmp_path, dryRun=True, logger=logger)

    assert source.exists()
    assert not (tmp_path / "project/requirements/requirementsIndex.md").exists()
    assert any("would rename" in message for message in logger.actions)


def testUnrecognisedNestedReadmeIsPreserved(tmp_path):
    source = tmp_path / "documentation/topic/README.md"
    _write(source, "# User documentation\n")

    layoutMigrate(tmp_path)

    assert source.exists()


def testIndexCollisionPreservesDifferentContent(tmp_path):
    source = tmp_path / "project/requirements/README.md"
    destination = tmp_path / "project/requirements/requirementsIndex.md"
    _write(
        source,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\nlegacy\n",
    )
    _write(destination, "# Requirements\ncanonical\n")

    layoutMigrate(tmp_path)

    assert source.exists()
    assert destination.read_text(encoding="utf-8") == "# Requirements\ncanonical\n"


def testRequirementDirectoryMigratesToFlatSpecification(tmp_path):
    source = tmp_path / "project/requirements/features/003-viewManagement/README.md"
    destination = tmp_path / "project/requirements/features/003-viewManagement.md"
    _write(source, "# 003: View management\n\n## Status\n\nToDo\n")

    layoutMigrate(tmp_path)

    assert destination.exists()
    assert not source.exists()
    assert not source.parent.exists()


def testRequirementDirectoryWithExtraContentIsPreserved(tmp_path):
    source = tmp_path / "project/requirements/features/003-viewManagement/README.md"
    extra = source.parent / "notes.md"
    _write(source, "# 003: View management\n")
    _write(extra, "notes\n")

    layoutMigrate(tmp_path)

    assert source.exists()
    assert extra.exists()
    assert not (
        tmp_path / "project/requirements/features/003-viewManagement.md"
    ).exists()


def testPromptDirectoryMigratesWhenRequirementExists(tmp_path):
    feature = tmp_path / "project/requirements/features/003-viewManagement.md"
    source = tmp_path / "project/requirements/prompt/003-viewManagement/README.md"
    destination = tmp_path / "project/requirements/prompt/003-viewManagement.md"
    _write(feature, "# 003: View management\n")
    _write(source, "Requirement: 003\nRole: implement\n")

    layoutMigrate(tmp_path)

    assert destination.exists()
    assert not source.parent.exists()


def testHistoricalSinglePromptFileMigrates(tmp_path):
    feature = tmp_path / "project/requirements/features/001-handbookFoundation.md"
    source = tmp_path / "project/requirements/prompt/001-handbookFoundation/refine.md"
    destination = tmp_path / "project/requirements/prompt/001-handbookFoundation.md"
    _write(feature, "# 001: Handbook foundation\n")
    _write(source, "# Refine handbook foundation\n")

    layoutMigrate(tmp_path)

    assert destination.read_text(encoding="utf-8") == "# Refine handbook foundation\n"
    assert not source.parent.exists()


def testHistoricalMultiPromptDirectoryIsPreserved(tmp_path):
    feature = tmp_path / "project/requirements/features/001-handbookFoundation.md"
    refine = tmp_path / "project/requirements/prompt/001-handbookFoundation/refine.md"
    review = tmp_path / "project/requirements/prompt/001-handbookFoundation/review.md"
    _write(feature, "# 001: Handbook foundation\n")
    _write(refine, "# Refine\n")
    _write(review, "# Review\n")

    layoutMigrate(tmp_path)

    assert refine.exists()
    assert review.exists()
    assert not (
        tmp_path / "project/requirements/prompt/001-handbookFoundation.md"
    ).exists()


def testPromptDirectoryWithoutRequirementIsPreserved(tmp_path):
    source = tmp_path / "project/requirements/prompt/003-viewManagement/README.md"
    _write(source, "Requirement: 003\nRole: implement\n")

    layoutMigrate(tmp_path)

    assert source.exists()
    assert not (tmp_path / "project/requirements/prompt/003-viewManagement.md").exists()


def testReferencePathsAreUpdated(tmp_path):
    document = tmp_path / "README.md"
    _write(
        document,
        "[Requirements](project/requirements/folderIndex.md)\n"
        "[ADRs](project/adr/folderIndex.md)\n",
    )

    layoutMigrate(tmp_path)

    text = document.read_text(encoding="utf-8")
    assert "project/requirements/requirementsIndex.md" in text
    assert "project/adr/adrIndex.md" in text


def testMigrationIsIdempotent(tmp_path):
    source = tmp_path / "project/requirements/README.md"
    _write(
        source,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )

    layoutMigrate(tmp_path)
    first = (tmp_path / "project/requirements/requirementsIndex.md").read_text(
        encoding="utf-8"
    )
    layoutMigrate(tmp_path)
    second = (tmp_path / "project/requirements/requirementsIndex.md").read_text(
        encoding="utf-8"
    )

    assert first == second


def testGeneratedCacheReadmeIsIgnoredByDocumentationCheck(tmp_path):
    """Generated cache README files must not trigger DOC-005."""
    from organiseMyProjects import agentCheck

    _write(tmp_path / "README.md", "# Project\n")
    _write(tmp_path / ".pytest_cache/README.md", "# pytest cache\n")

    validator = agentCheck.AgentCheckValidator(tmp_path)
    validator._checkDocumentation()

    failures = [
        item
        for item in validator.report.findings
        if getattr(item, "ruleId", None) == "DOC-005"
    ]
    assert failures == []


def _scaffoldCreate(tmp_path: Path) -> Path:
    from unittest.mock import patch

    from organiseMyProjects.manageProject import createProject

    project = tmp_path / "layoutProject"
    with patch("organiseMyProjects.manageProject.subprocess.run"):
        createProject(str(project))
    return project


def testNewScaffoldUsesNamedIndexesWithoutNestedReadmes(tmp_path):
    """Requirement 004 criteria 3 and 4 on a real createProject scaffold."""
    project = _scaffoldCreate(tmp_path)

    assert (project / "project/requirements/requirementsIndex.md").is_file()
    assert (project / "project/adr/adrIndex.md").is_file()
    assert list(project.rglob("folderIndex.md")) == []
    assert [path for path in project.rglob("README.md")] == [project / "README.md"]


def testNewScaffoldPassesLayoutChecks(tmp_path):
    """Requirement 004 criterion 16: check accepts a fresh scaffold's named indexes."""
    from organiseMyProjects.agentCheck import AgentCheckValidator

    project = _scaffoldCreate(tmp_path)
    report = AgentCheckValidator(project).runAll()

    assert report.failures == []


def testNewScaffoldRequirementListingIsCheckedAgainstNamedIndex(tmp_path):
    """Check reads requirementsIndex.md when matching requirement files."""
    from organiseMyProjects.agentCheck import AgentCheckValidator

    project = _scaffoldCreate(tmp_path)
    requirements = project / "project/requirements"
    _write(requirements / "features/001-listedThing.md", "# 001\n\n## Status\n\nToDo\n")
    _write(
        requirements / "features/002-unlistedThing.md", "# 002\n\n## Status\n\nToDo\n"
    )
    index = requirements / "requirementsIndex.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "| 001 | [Listed](features/001-listedThing.md) | Listed. | ToDo |"
        " Not required | Not required |\n",
        encoding="utf-8",
    )

    report = AgentCheckValidator(project).runAll()
    unlisted = [
        finding.filePath.name
        for finding in report.failures
        if finding.ruleId == "REQ-001"
    ]

    assert unlisted == ["002-unlistedThing.md"]


def testNewScaffoldNestedReadmeIsReported(tmp_path):
    """Check reports an OMPR-owned nested README mistake in a fresh scaffold."""
    from organiseMyProjects.agentCheck import AgentCheckValidator

    project = _scaffoldCreate(tmp_path)
    _write(
        project / "project/requirements/features/003-viewManagement/README.md",
        "# 003\n",
    )

    report = AgentCheckValidator(project).runAll()

    assert any(finding.ruleId == "DOC-005" for finding in report.failures)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("009-read-inbox-filing.md", "009-readInboxFiling.md"),
        ("MA-012-rolling-imap-retention.md", "012-rollingImapRetention.md"),
        ("MA-011-sessionCredentialCache.md", "011-sessionCredentialCache.md"),
        (
            "004-requirementDocumentationLayout.md",
            "004-requirementDocumentationLayout.md",
        ),
        ("notARequirement.md", None),
    ],
)
def testRequirementFilenameSuggest(name, expected):
    assert requirementFilenameSuggest(name) == expected
