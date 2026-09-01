from pathlib import Path

from organiseMyProjects.manageProject import updateProject


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
