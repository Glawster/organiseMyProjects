from pathlib import Path

from organiseMyProjects.manageProject import (
    ADR_INDEX_CONTENT,
    REQUIREMENTS_INDEX_CONTENT,
    migrateProject,
    updateProject,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def testUpdateProjectMigratesRequirementsReadmeToNamedIndex(tmp_path):
    source = tmp_path / "project/requirements/README.md"
    destination = tmp_path / "project/requirements/requirementsIndex.md"
    _write(
        source,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )

    updateProject(tmp_path)

    assert not source.exists()
    assert destination.exists()


def testUpdateProjectMigratesMistakenFolderIndexes(tmp_path):
    requirementsSource = tmp_path / "project/requirements/folderIndex.md"
    adrSource = tmp_path / "project/adr/folderIndex.md"
    _write(
        requirementsSource,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )
    _write(
        adrSource,
        "# Architecture Decision Records\n\nNext available number: 002\n\n## Decision index\n",
    )

    updateProject(tmp_path)

    assert not requirementsSource.exists()
    assert not adrSource.exists()
    assert (tmp_path / "project/requirements/requirementsIndex.md").exists()
    assert (tmp_path / "project/adr/adrIndex.md").exists()


def testUpdateProjectNamedIndexCleanupIsIdempotent(tmp_path):
    source = tmp_path / "project/requirements/README.md"
    destination = tmp_path / "project/requirements/requirementsIndex.md"
    _write(
        source,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n",
    )

    updateProject(tmp_path)
    first = destination.read_text(encoding="utf-8")
    updateProject(tmp_path)

    assert destination.read_text(encoding="utf-8") == first
    assert not source.exists()


def _files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*")}


def testMigrateProjectCreatesNamedIndexes(tmp_path):
    migrateProject(tmp_path, dryRun=True)
    assert _files(tmp_path) == set()

    migrateProject(tmp_path)

    files = _files(tmp_path)
    assert "project/requirements/requirementsIndex.md" in files
    assert "project/adr/adrIndex.md" in files
    assert "project/requirements/README.md" not in files
    assert "project/adr/README.md" not in files
    # The prompt-index step appends its own section to the requirements index.
    assert (
        (tmp_path / "project/requirements/requirementsIndex.md")
        .read_text(encoding="utf-8")
        .startswith(REQUIREMENTS_INDEX_CONTENT)
    )
    assert (tmp_path / "project/adr/adrIndex.md").read_text(
        encoding="utf-8"
    ) == ADR_INDEX_CONTENT


def testMigrateProjectDryRunReportsNamedIndexes(tmp_path, caplog):
    """The dry run reports the files a confirmed run leaves behind."""
    with caplog.at_level("INFO"):
        migrateProject(tmp_path, dryRun=True)

    assert "requirementsIndex.md" in caplog.text
    assert "adrIndex.md" in caplog.text
    assert "requirements/README.md" not in caplog.text
    assert "adr/README.md" not in caplog.text


def testMigrateProjectRenamesLegacyIndexWithRows(tmp_path, caplog):
    """A real legacy index is renamed, not shadowed by an empty new index."""
    legacy = tmp_path / "project/requirements/README.md"
    row = "| 001 | [First](features/001-first.md) | One. | ToDo | | |\n"
    _write(
        legacy,
        "# Requirements\n\nNext available number: 002\n\n## Requirement index\n\n"
        + row,
    )
    with caplog.at_level("INFO"):
        migrateProject(tmp_path, dryRun=True)
    planned = caplog.text.splitlines()
    assert not any(
        "would create" in line and "requirementsIndex.md" in line for line in planned
    )
    assert any("would rename" in line and "README.md" in line for line in planned)
    assert not (tmp_path / "project/requirements/requirementsIndex.md").exists()

    migrateProject(tmp_path)

    assert not legacy.exists()
    index = tmp_path / "project/requirements/requirementsIndex.md"
    assert row.strip() in index.read_text(encoding="utf-8")
