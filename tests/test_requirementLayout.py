from pathlib import Path

from organiseMyProjects.requirementLayout import layoutMigrate


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


def test_indexReadmeMigratesToRequirementsIndex(tmp_path):
    source = tmp_path / "project/requirements/README.md"
    destination = tmp_path / "project/requirements/requirementsIndex.md"
    _write(
        source,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )

    layoutMigrate(tmp_path)

    assert not source.exists()
    assert destination.exists()


def test_historicalRequirementsReadmeMigrates(tmp_path):
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


def test_historicalAdrReadmeMigrates(tmp_path):
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


def test_mistakenFolderIndexesMigrateToNamedIndexes(tmp_path):
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


def test_canonicalNamedIndexesArePreserved(tmp_path):
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


def test_indexMigrationDryRunDoesNotChangeFiles(tmp_path):
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


def test_unrecognisedNestedReadmeIsPreserved(tmp_path):
    source = tmp_path / "documentation/topic/README.md"
    _write(source, "# User documentation\n")

    layoutMigrate(tmp_path)

    assert source.exists()


def test_indexCollisionPreservesDifferentContent(tmp_path):
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


def test_requirementDirectoryMigratesToFlatSpecification(tmp_path):
    source = tmp_path / "project/requirements/features/003-viewManagement/README.md"
    destination = tmp_path / "project/requirements/features/003-viewManagement.md"
    _write(source, "# 003: View management\n\n## Status\n\nToDo\n")

    layoutMigrate(tmp_path)

    assert destination.exists()
    assert not source.exists()
    assert not source.parent.exists()


def test_requirementDirectoryWithExtraContentIsPreserved(tmp_path):
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


def test_promptDirectoryMigratesWhenRequirementExists(tmp_path):
    feature = tmp_path / "project/requirements/features/003-viewManagement.md"
    source = tmp_path / "project/requirements/prompt/003-viewManagement/README.md"
    destination = tmp_path / "project/requirements/prompt/003-viewManagement.md"
    _write(feature, "# 003: View management\n")
    _write(source, "Requirement: 003\nRole: implement\n")

    layoutMigrate(tmp_path)

    assert destination.exists()
    assert not source.parent.exists()


def test_historicalSinglePromptFileMigrates(tmp_path):
    feature = tmp_path / "project/requirements/features/001-handbookFoundation.md"
    source = tmp_path / "project/requirements/prompt/001-handbookFoundation/refine.md"
    destination = tmp_path / "project/requirements/prompt/001-handbookFoundation.md"
    _write(feature, "# 001: Handbook foundation\n")
    _write(source, "# Refine handbook foundation\n")

    layoutMigrate(tmp_path)

    assert destination.read_text(encoding="utf-8") == "# Refine handbook foundation\n"
    assert not source.parent.exists()


def test_historicalMultiPromptDirectoryIsPreserved(tmp_path):
    feature = tmp_path / "project/requirements/features/001-handbookFoundation.md"
    refine = tmp_path / "project/requirements/prompt/001-handbookFoundation/refine.md"
    review = tmp_path / "project/requirements/prompt/001-handbookFoundation/review.md"
    _write(feature, "# 001: Handbook foundation\n")
    _write(refine, "# Refine\n")
    _write(review, "# Review\n")

    layoutMigrate(tmp_path)

    assert refine.exists()
    assert review.exists()
    assert not (tmp_path / "project/requirements/prompt/001-handbookFoundation.md").exists()


def test_promptDirectoryWithoutRequirementIsPreserved(tmp_path):
    source = tmp_path / "project/requirements/prompt/003-viewManagement/README.md"
    _write(source, "Requirement: 003\nRole: implement\n")

    layoutMigrate(tmp_path)

    assert source.exists()
    assert not (tmp_path / "project/requirements/prompt/003-viewManagement.md").exists()


def test_referencePathsAreUpdated(tmp_path):
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


def test_migrationIsIdempotent(tmp_path):
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
