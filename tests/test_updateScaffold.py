"""Existing repositories can acquire the required OMP context safely."""

import subprocess

import pytest

from organiseMyProjects.agentCheck import AgentCheckValidator
from organiseMyProjects.manageProject import main, updateProject


@pytest.mark.parametrize("marker", [None, "package.json", "pyproject.toml", "main.py"])
def testExistingRepositoryUpdateThenCheck(tmp_path, monkeypatch, marker):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    if marker:
        (tmp_path / marker).write_text("")
    monkeypatch.chdir(tmp_path)

    main(["update", "-y"])

    report = AgentCheckValidator(tmp_path).runAll()
    assert not report.failures, report.findings
    # Actual project test commands require the owner's input, explicitly explained
    # by update; no invented command is inserted merely to silence this warning.
    assert {finding.ruleId for finding in report.warnings} <= {"DOC-003"}
    assert "## Status\n\nIdle" in (tmp_path / "project/currentIncrement.md").read_text()


def testUpdatePreservesContextAndIsIdempotent(tmp_path):
    paths = [
        "README.md",
        ".github/additional-instructions.md",
        "project/currentIncrement.md",
    ]
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Custom {relative}\n")
    updateProject(tmp_path)
    snapshot = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    updateProject(tmp_path)
    assert snapshot == {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in snapshot
    }
    for relative in paths:
        assert (tmp_path / relative).read_text() == f"# Custom {relative}\n"


def testUpdateScaffoldDryRun(tmp_path, caplog):
    import logging

    with caplog.at_level(logging.INFO):
        updateProject(tmp_path, dryRun=True)
    assert list(tmp_path.iterdir()) == []
    for relative in ["README.md", "additional-instructions.md", "currentIncrement.md"]:
        assert relative in caplog.text
    assert "project action required" in caplog.text


@pytest.mark.parametrize(
    "missing",
    ["README.md", ".github/additional-instructions.md", "project/currentIncrement.md"],
)
def testUpdateRepairsPartialScaffold(tmp_path, missing):
    updateProject(tmp_path)
    (tmp_path / missing).unlink()
    updateProject(tmp_path)
    assert (tmp_path / missing).is_file()
    assert not AgentCheckValidator(tmp_path).runAll().failures
