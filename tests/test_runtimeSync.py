"""Tests for managed OMPR runtime synchronisation."""

from pathlib import Path

from organiseMyProjects import runtimeSync as sync


def testRuntimeDryRun(tmp_path: Path):
    root = tmp_path / "consumer"
    root.mkdir()
    planned = sync.runtimeSync(root)
    assert all(item.action == "create" for item in planned)
    assert not (root / "ompr").exists()
