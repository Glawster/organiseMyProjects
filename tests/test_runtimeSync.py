"""Tests for managed OMPR runtime synchronisation."""

from pathlib import Path

from organiseMyProjects import runtimeSync as sync


def testRuntimeDryRun(tmp_path: Path):
    root = tmp_path / "consumer"
    root.mkdir()
    planned = sync.runtimeSync(root)
    assert all(item.action == "create" for item in planned)
    assert not (root / "ompr").exists()


def testInstallAndIdempotence(tmp_path: Path):
    root = tmp_path / "consumer"
    root.mkdir()
    installed = sync.runtimeSync(root, dryRun=False)
    assert all(item.action == "create" for item in installed)
    for name in ("__init__.py", *sync.RUNTIME_MANIFEST):
        file = root / "ompr" / name
        assert file.is_file()
        assert sync.MARKER in file.read_text()
    assert all(item.action == "unchanged" for item in sync.runtimePlan(root))


def testManagedUpdatesAndProjectOwnedCollision(tmp_path: Path):
    root = tmp_path / "consumer"
    root.mkdir()
    sync.runtimeSync(root, dryRun=False)
    deployed = root / "ompr" / "logUtils.py"
    deployed.write_text(deployed.read_text() + "\n# local edit\n")
    assert any(item.action == "update" for item in sync.runtimePlan(root))
    sync.runtimeSync(root, dryRun=False)
    assert "local edit" not in deployed.read_text()
    deployed.write_text("# project owned\n")
    before = {p.name: p.read_bytes() for p in deployed.parent.iterdir()}
    blocked = sync.runtimeSync(root, dryRun=False)
    assert any(item.action == "blocked" for item in blocked)
    assert {p.name: p.read_bytes() for p in deployed.parent.iterdir()} == before


def testBatchDoesNotTouchOtherProjects(tmp_path: Path):
    roots = [tmp_path / name for name in ("one", "two", "other")]
    for root in roots:
        root.mkdir()
    results = sync.runtimeBatch(roots[:2], dryRun=False)
    assert len(results) == 2
    assert all((root / "ompr" / "logUtils.py").exists() for root in roots[:2])
    assert list(roots[2].iterdir()) == []
