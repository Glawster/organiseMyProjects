"""Requirement 016: deterministic requirement and prompt naming correction."""

import subprocess
from pathlib import Path

from organiseMyProjects.manageProject import updateProject
from organiseMyProjects.requirementNaming import requirementNamesCorrect

_INDEX = """# Requirements

Next available number: 013

## Requirement index

| Req ID | Requirement | Description | Status | Agent Prompt | Architecture Decisions |
| --- | --- | --- | --- | --- | --- |
| 009 | [Read Inbox filing](features/009-read-inbox-filing.md) | Filing. | InProgress | [Prompt](../prompts/009-read-inbox-filing.md) | Not required |
| MA-012 | [Rolling retention](features/MA-012-rolling-imap-retention.md) | Retention. | InProgress | Not recorded | Not required |
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _legacyRepo(root: Path) -> Path:
    """Reproduce the drift found in mailAgent before its 2026-10-20 correction."""
    _write(root / "project/requirements/requirementsIndex.md", _INDEX)
    _write(
        root / "project/requirements/features/009-read-inbox-filing.md",
        "# REQ-009 - Read Inbox filing\n\n## Status\n\nInProgress\n\n"
        "## Change history\n\n- 2026-10-08: created.\n",
    )
    _write(
        root / "project/requirements/features/MA-012-rolling-imap-retention.md",
        "# MA-012 Rolling IMAP retention\n\nStatus: InProgress\n\n## Purpose\n\n"
        "See [filing](009-read-inbox-filing.md#core-filing-rule). "
        "MA-012 keeps recent mail.\n",
    )
    _write(
        root / "project/prompts/009-read-inbox-filing.md",
        "# Prompt\n\nImplement [009](../requirements/features/009-read-inbox-filing.md).\n",
    )
    _write(
        root / "README.md",
        "# Demo\n\n## Documentation\n\n"
        "- [Retention](project/requirements/features/MA-012-rolling-imap-retention.md)\n"
        "- [External](https://example.com/009-read-inbox-filing.md)\n",
    )
    _write(root / "src/demo.py", '"""Implements MA-012 retention."""\n')
    return root


def _tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }


def testDryRunReportsWithoutChanging(tmp_path):
    root = _legacyRepo(tmp_path)
    before = _tree(root)

    result = requirementNamesCorrect(root, dryRun=True)

    assert _tree(root) == before
    names = {(s.name, d.name) for s, d in result.renames.items()}
    assert ("MA-012-rolling-imap-retention.md", "012-rollingImapRetention.md") in names
    assert ("009-read-inbox-filing.md", "009-readInboxFiling.md") in names
    assert result.changed


def testConfirmedCorrectionRenamesNormalisesAndRelinks(tmp_path):
    root = _legacyRepo(tmp_path)

    requirementNamesCorrect(root, dryRun=False)

    features = root / "project/requirements/features"
    assert sorted(path.name for path in features.iterdir()) == [
        "009-readInboxFiling.md",
        "012-rollingImapRetention.md",
    ]
    retention = (features / "012-rollingImapRetention.md").read_text(encoding="utf-8")
    assert retention.startswith(
        "# 012: Rolling IMAP retention\n\n## Status\n\nInProgress\n"
    )
    assert "](009-readInboxFiling.md#core-filing-rule)" in retention
    assert "(was `MA-012-rolling-imap-retention.md`)" in retention
    filing = (features / "009-readInboxFiling.md").read_text(encoding="utf-8")
    assert filing.startswith("# 009: Read Inbox filing\n")
    assert "- 2026-10-08: created.\n- " in filing

    index = (root / "project/requirements/requirementsIndex.md").read_text(
        encoding="utf-8"
    )
    assert "| 012 | [Rolling retention](features/012-rollingImapRetention.md)" in index
    assert "[Prompt](prompt/009-readInboxFiling.md)" in index
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "(project/requirements/features/012-rollingImapRetention.md)" in readme
    assert "https://example.com/009-read-inbox-filing.md" in readme


def testPromptsMoveBesideTheirRecordAndLegacyDirectoryGoes(tmp_path):
    root = _legacyRepo(tmp_path)

    requirementNamesCorrect(root, dryRun=False)

    prompt = root / "project/requirements/prompt/009-readInboxFiling.md"
    assert prompt.is_file()
    assert "](../features/009-readInboxFiling.md)" in prompt.read_text(encoding="utf-8")
    assert not (root / "project/prompts").exists()


def testMentionsOutsideLinksAreReportedNotRewritten(tmp_path):
    root = _legacyRepo(tmp_path)

    result = requirementNamesCorrect(root, dryRun=False)

    assert (root / "src/demo.py").read_text(encoding="utf-8") == (
        '"""Implements MA-012 retention."""\n'
    )
    assert "review mention of 'MA-012' at src/demo.py:1" in result.mentions
    assert any(
        "project/requirements/features/012-rollingImapRetention.md" in mention
        for mention in result.mentions
    )
    # Headings, index IDs and the correction's own notes are not reported.
    assert not any("requirementsIndex.md" in mention for mention in result.mentions)
    assert not any(
        "features/009-readInboxFiling.md" in mention for mention in result.mentions
    )


def testCollisionLeavesBothFilesUnchanged(tmp_path):
    root = _legacyRepo(tmp_path)
    existing = root / "project/requirements/features/009-readInboxFiling.md"
    _write(existing, "# 009: Different content\n")
    legacy = root / "project/requirements/features/009-read-inbox-filing.md"
    legacyText = legacy.read_text(encoding="utf-8")

    result = requirementNamesCorrect(root, dryRun=False)

    assert existing.read_text(encoding="utf-8") == "# 009: Different content\n"
    assert legacy.read_text(encoding="utf-8") == legacyText
    assert any("already exists" in message for message in result.collisions)


def testCorrectionIsIdempotent(tmp_path):
    root = _legacyRepo(tmp_path)
    requirementNamesCorrect(root, dryRun=False)
    after = _tree(root)

    again = requirementNamesCorrect(root, dryRun=False)

    assert not again.changed
    assert _tree(root) == after


def testTrackedFilesMoveWithGitHistory(tmp_path):
    root = _legacyRepo(tmp_path)
    git = ["git", "-C", str(root)]
    subprocess.run(git + ["init", "-q"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(
        git + ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"],
        check=True,
    )

    requirementNamesCorrect(root, dryRun=False)

    status = subprocess.run(
        git + ["status", "--porcelain"], capture_output=True, text=True, check=True
    ).stdout
    assert (
        "R  project/requirements/features/MA-012-rolling-imap-retention.md -> "
        "project/requirements/features/012-rollingImapRetention.md" in status
        or "RM project/requirements/features/MA-012-rolling-imap-retention.md -> "
        "project/requirements/features/012-rollingImapRetention.md" in status
    )


def testUpdateProjectAppliesCorrectionOnlyWhenConfirmed(tmp_path):
    root = _legacyRepo(tmp_path)
    legacy = root / "project/requirements/features/MA-012-rolling-imap-retention.md"

    updateProject(root, dryRun=True)
    assert legacy.exists()

    updateProject(root)
    assert not legacy.exists()
    assert (root / "project/requirements/features/012-rollingImapRetention.md").exists()
