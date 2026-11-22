"""Behavioural evidence for saved opt-in deployment and recoverable cleanup."""

import base64
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import syncAgentInstructions as sync
from organiseMyProjects import manageProject
from organiseMyProjects.runtimeDeployment import runtimeFiles
from organiseMyProjects.runtimePreference import (
    PREFERENCE_PATH,
    preferenceRead,
    runtimeReconcile,
)
from organiseMyProjects.runtimeSync import runtimeSync


def _snapshot(root):
    return {
        str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def _reconcile(root, choice=None, dryRun=False):
    return runtimeReconcile(root, choice, dryRun=dryRun, logger=MagicMock())


@pytest.mark.parametrize("enabled", [False, True])
def testCreateModeControlsImportsPackagingAndSavedChoice(tmp_path, enabled):
    root = tmp_path / "sample"
    with patch.object(manageProject.subprocess, "run"):
        manageProject.createProject(root, localRuntime=enabled, includeUi=True)
    metadata = (root / "pyproject.toml").read_text()
    entry = (root / "sample/__main__.py").read_text()
    assert (root / "ompr").exists() is enabled
    assert preferenceRead((root / PREFERENCE_PATH).read_text()) is enabled
    assert ('"ompr"' in metadata) is enabled
    assert ('ompr = ["*.sh"]' in metadata) is enabled
    expected = "ompr" if enabled else "organiseMyProjects"
    assert f"from {expected}.logUtils import" in entry
    assert ('dependencies = ["organiseMyProjects"]' in metadata) is not enabled
    assert f"`{expected}.logUtils`" in (root / "README.md").read_text()


def testDefaultCreateOmitsRuntime(tmp_path):
    root = tmp_path / "defaultApp"
    with patch.object(manageProject.subprocess, "run"):
        manageProject.createProject(root)
    assert not (root / "ompr").exists()
    assert "localRuntime: false" in (root / PREFERENCE_PATH).read_text()


def testPersistEnableDisableReenableAndRepeat(tmp_path):
    config = tmp_path / PREFERENCE_PATH
    config.parent.mkdir()
    config.write_text("name: example\n# keep me\ncustom: 42\n")
    assert _reconcile(tmp_path, True)
    assert _reconcile(tmp_path)
    before = _snapshot(tmp_path)
    assert _reconcile(tmp_path)
    assert _snapshot(tmp_path) == before
    helper = tmp_path / "ompr/logUtils.py"
    helper.write_text(helper.read_text() + "\n# locally modified\n")
    original = helper.read_bytes()
    assert not _reconcile(tmp_path, False)
    assert not (tmp_path / "ompr").exists()
    backups = list((tmp_path / "output/omprRuntimeBackups").glob("*/logUtils.py"))
    assert len(backups) == 1 and backups[0].read_bytes() == original
    assert "# keep me\ncustom: 42\n" in config.read_text()
    assert not _reconcile(tmp_path)
    after = _snapshot(tmp_path)
    _reconcile(tmp_path)
    assert _snapshot(tmp_path) == after
    assert _reconcile(tmp_path, True)
    assert helper.is_file()


@pytest.mark.parametrize("legacy", [False, True])
def testUnconfiguredLegacyCopiesAreRemoved(tmp_path, legacy):
    if legacy:
        runtimeSync(tmp_path, dryRun=False)
    else:
        _reconcile(tmp_path, True)
        (tmp_path / PREFERENCE_PATH).unlink()
    assert not _reconcile(tmp_path)
    assert not (tmp_path / "ompr").exists()


@pytest.mark.parametrize("choice", [False, True, None])
def testDryRunDoesNotChangeAnything(tmp_path, choice):
    _reconcile(tmp_path, True)
    if choice is None:
        (tmp_path / PREFERENCE_PATH).unlink()
    before = _snapshot(tmp_path)
    _reconcile(tmp_path, choice, dryRun=True)
    assert _snapshot(tmp_path) == before
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "text",
    [
        "localRuntime: yes\n",
        "localRuntime: 'false'\n",
        "localRuntime: 1\n",
        "localRuntime: null\n",
        "localRuntime:\n",
        "localRuntime: true\nlocalRuntime: false\n",
        "  localRuntime: true\n",
    ],
)
def testInvalidSettingsFailBeforeAnyMutation(tmp_path, text):
    config = tmp_path / PREFERENCE_PATH
    config.parent.mkdir()
    config.write_text(text)
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="localRuntime"):
        manageProject.updateProject(tmp_path, localRuntime=True)
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "relative,content",
    [
        ("app.py", "from ompr.logUtils import getLogger\n"),
        ("otherPackage/nested.py", "import ompr\n"),
        ("scripts/start.sh", 'source "$root/ompr/logUtils.sh"\n'),
        ("pyproject.toml", '[tool.setuptools]\npackages = ["app", "ompr"]\n'),
        (".github/workflows/deploy.yml", "run: cp -r ompr target/\n"),
        ("custom.py", "import importlib\nimportlib.import_module('ompr.logUtils')\n"),
    ],
)
def testReferencesBlockWholeUpdateAndKeepPreference(tmp_path, relative, content):
    _reconcile(tmp_path, True)
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="cleanup blocked") as error:
        manageProject.updateProject(tmp_path, localRuntime=False)
    assert relative in str(error.value)
    assert _snapshot(tmp_path) == before
    assert not (tmp_path / "output").exists()


def testUnknownContentAndLinksArePreserved(tmp_path):
    _reconcile(tmp_path, True)
    foreign = tmp_path / "ompr/custom.py"
    foreign.write_text("# project-owned\n")
    outside = tmp_path / "outside.txt"
    outside.write_text("keep\n")
    link = tmp_path / "ompr/logUtils.py"
    link.unlink()
    link.symlink_to(outside)
    reporter = MagicMock()
    runtimeReconcile(tmp_path, False, dryRun=False, logger=reporter)
    assert foreign.read_text() == "# project-owned\n"
    assert link.is_symlink() and outside.read_text() == "keep\n"
    assert reporter.warning.call_count >= 2


@pytest.mark.parametrize("location", ["project", "output"])
def testConfigAndBackupSymlinksBlockBeforeCleanup(tmp_path, location):
    root = tmp_path / "app"
    root.mkdir()
    _reconcile(root, True)
    external = tmp_path / "outside"
    external.mkdir()
    path = root / location
    if path.exists():
        (external / "project.yaml").write_bytes((path / "project.yaml").read_bytes())
        (path / "project.yaml").unlink()
        path.rmdir()
    path.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        _reconcile(root, False)
    assert (root / "ompr/logUtils.py").is_file()
    assert list(external.iterdir()) == (
        [external / "project.yaml"] if location == "project" else []
    )


def testFailedBackupDoesNotRemoveAnyHelper(tmp_path, monkeypatch):
    _reconcile(tmp_path, True)
    monkeypatch.setattr(
        "organiseMyProjects.runtimePreference.shutil.copy2",
        MagicMock(side_effect=OSError("backup failed")),
    )
    with pytest.raises(OSError, match="backup failed"):
        _reconcile(tmp_path, False)
    assert all((tmp_path / path).is_file() for _, path in runtimeFiles())
    assert preferenceRead((tmp_path / PREFERENCE_PATH).read_text())


@pytest.mark.parametrize("command", ["create", "update", "sync"])
def testConflictingFlagsRejectedWithoutMutation(tmp_path, command):
    with pytest.raises(SystemExit):
        manageProject.main(
            [
                command,
                "--project",
                str(tmp_path / "app"),
                "--runtime",
                "--no-runtime",
                "--confirm",
            ]
        )
    assert list(tmp_path.iterdir()) == []


def testPublicLocalSyncAndUpdateRespectSavedPreference(tmp_path):
    assert (
        manageProject.main(
            ["sync", "--project", str(tmp_path), "--runtime", "--confirm"]
        )
        == 0
    )
    manageProject.updateProject(tmp_path)
    assert (tmp_path / "ompr/logUtils.py").exists()
    manageProject.main(
        ["update", "--project", str(tmp_path), "--no-runtime", "--confirm"]
    )
    assert not (tmp_path / "ompr").exists()
    manageProject.updateProject(tmp_path)
    assert not (tmp_path / "ompr").exists()


def _remoteSnapshot(root):
    entries = []
    contents = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        entries.append(
            {
                "path": relative,
                "type": "tree" if path.is_dir() else "blob",
                "mode": "040000" if path.is_dir() else "100644",
            }
        )
        if path.is_file():
            contents[relative] = path.read_bytes()
    return {"tree": entries}, contents


def testRemoteDisablePlansAtomicPreferenceBackupAndDeletions(tmp_path, monkeypatch):
    _reconcile(tmp_path, True)
    snapshot, contents = _remoteSnapshot(tmp_path)
    monkeypatch.setattr(
        sync,
        "getRemoteFile",
        lambda repo, path, headers, ref: {
            "content": base64.b64encode(contents[path]).decode()
        },
    )
    updates = sync._runtimeUpdatesBuild(
        "owner/app", "head", snapshot, {}, enabled=False
    )
    assert {item["path"] for item in updates if item.get("sha", "present") is None} == {
        path.as_posix() for _, path in runtimeFiles()
    }
    config = next(
        item for item in updates if item["path"] == PREFERENCE_PATH.as_posix()
    )
    assert config["content"] == "localRuntime: false\n"
    backups = [
        item
        for item in updates
        if item["path"].startswith("output/omprRuntimeBackups/")
    ]
    assert len(backups) == len(runtimeFiles())
    for item in backups:
        assert item["content"].encode() == contents["ompr/" + Path(item["path"]).name]


def testRemoteDisableBlocksUnmigratedCode(tmp_path, monkeypatch):
    _reconcile(tmp_path, True)
    (tmp_path / "entry.py").write_text("import ompr\n")
    snapshot, contents = _remoteSnapshot(tmp_path)
    monkeypatch.setattr(
        sync,
        "getRemoteFile",
        lambda repo, path, headers, ref: {
            "content": base64.b64encode(contents[path]).decode()
        },
    )
    monkeypatch.setattr(
        sync, "_runtimeSnapshotLoad", lambda *args: ("main", "head", snapshot)
    )
    post = MagicMock()
    monkeypatch.setattr(sync.requests, "post", post)
    assert (
        sync.runtimeSyncRepo(
            "owner/app", "sync/test", False, {}, MagicMock(), set(), enabled=False
        )
        == "failed"
    )
    post.assert_not_called()


def testRemoteOmittedRuntimeDoesNotReconcile(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["syncAgentInstructions.py", "--repo", "owner/app"]
    )
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    monkeypatch.setattr(sync, "configSaveToken", MagicMock())
    monkeypatch.setattr(sync, "getRepoRole", lambda *args: "")
    monkeypatch.setattr(sync, "getTargetRepos", lambda *args: ["owner/app"])
    monkeypatch.setattr(sync, "syncRepo", lambda *args, **kwargs: "skipped")
    runtime = MagicMock()
    monkeypatch.setattr(sync, "runtimeSyncRepo", runtime)
    sync.main()
    runtime.assert_not_called()


def testDefaultWheelRunsWithDeclaredInstalledToolkit(tmp_path):
    """Build both real distributions and execute the consumer away from source."""
    pytest.importorskip("build", reason="build is required for distribution evidence")
    pytest.importorskip(
        "setuptools", reason="setuptools is required for distribution evidence"
    )
    pytest.importorskip("wheel", reason="wheel is required for distribution evidence")
    root = tmp_path / "defaultApp"
    with patch.object(manageProject.subprocess, "run"):
        manageProject.createProject(root)
    # Exercise the generated optional-UI entry point with neither UI installed.
    (root / "defaultApp/__main__.py").write_text(manageProject.PACKAGE_MAIN_CONTENT)
    distribution = tmp_path / "dist"
    toolkit = Path(manageProject.__file__).resolve().parent.parent
    for source in (toolkit, root):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--no-isolation",
                "--outdir",
                str(distribution),
            ],
            cwd=source,
            check=True,
            capture_output=True,
            text=True,
        )
    installed = tmp_path / "installed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--target",
            str(installed),
            *map(str, distribution.glob("*.whl")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    import zipfile

    with zipfile.ZipFile(next(distribution.glob("defaultapp-*.whl"))) as archive:
        assert not any(name.startswith("ompr/") for name in archive.namelist())
        metadata = archive.read(
            next(
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/METADATA")
            )
        ).decode()
        assert "Requires-Dist: organiseMyProjects" in metadata
    script = """
import pathlib, runpy, sys
sys.path.insert(0, sys.argv[1])
import organiseMyProjects.logUtils as logs
original = logs.setApplication
logDirectory = pathlib.Path(sys.argv[2])
logs.setApplication = lambda name: original(name, logDirectory)
assert logs.__file__.startswith(sys.argv[1])
sys.argv = ['defaultApp']
runpy.run_module('defaultApp', run_name='__main__')
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            script,
            str(installed),
            str(tmp_path / "logs"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "no ui scaffold installed" in result.stderr
    assert not (installed / "ompr").exists()


def testPublicCreateRuntimeFlagPersistsThroughUpdate(tmp_path):
    root = tmp_path / "flagApp"
    with patch.object(manageProject.subprocess, "run"):
        manageProject.main(["create", "--project", str(root), "--runtime", "--confirm"])
    manageProject.main(["update", "--project", str(root), "--confirm"])
    assert (root / "ompr/logUtils.py").is_file()
    assert preferenceRead((root / PREFERENCE_PATH).read_text())


def testSourceSymlinkBlocksRemoval(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    _reconcile(root, True)
    external = tmp_path / "external"
    external.mkdir()
    (external / "entry.py").write_text("import ompr\n")
    (root / "code").symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink directory"):
        _reconcile(root, False)
    assert (root / "ompr/logUtils.py").is_file()


def testFlowMappingPreferenceRejected(tmp_path):
    config = tmp_path / PREFERENCE_PATH
    config.parent.mkdir()
    config.write_text("{localRuntime: true}\n")
    with pytest.raises(ValueError, match="flow mapping"):
        _reconcile(tmp_path)


def testExcludedProjectRolesDoNotReceiveRuntime(tmp_path):
    root = tmp_path / "addon"
    root.mkdir()
    (root / "addon.toc").write_text("## Interface: 120001\n")
    with pytest.raises(ValueError, match="wow addons"):
        _reconcile(root, True)
    assert not (root / PREFERENCE_PATH).exists()
    canonical = Path(manageProject.__file__).resolve().parent.parent
    config = canonical / PREFERENCE_PATH
    before = config.read_bytes() if config.exists() else None
    with pytest.raises(ValueError, match="canonical"):
        _reconcile(canonical, True)
    assert (config.read_bytes() if config.exists() else None) == before


def testPreferenceCommentsAndLineEndingsRemain(tmp_path):
    config = tmp_path / PREFERENCE_PATH
    config.parent.mkdir()
    config.write_bytes(
        b"name: example\r\nlocalRuntime: true # intentional\r\nother: kept\r\n"
    )
    _reconcile(tmp_path, False)
    assert (
        config.read_bytes()
        == b"name: example\r\nlocalRuntime: false # intentional\r\nother: kept\r\n"
    )


def testRemoteBlockerPreventsInstructionWrites(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "syncAgentInstructions.py",
            "--repo",
            "owner/app",
            "--no-runtime",
            "--confirm",
        ],
    )
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    monkeypatch.setattr(sync, "configSaveToken", MagicMock())
    monkeypatch.setattr(sync, "getTargetRepos", lambda *args: ["owner/app"])
    reconcile = MagicMock(return_value="failed")
    instructions = MagicMock()
    monkeypatch.setattr(sync, "runtimeSyncRepo", reconcile)
    monkeypatch.setattr(sync, "syncRepo", instructions)
    sync.main()
    assert reconcile.call_args.kwargs["enabled"] is False
    instructions.assert_not_called()


def testNoRuntimeFlagForwardedToRemote(monkeypatch):
    from types import SimpleNamespace

    captured = []
    monkeypatch.setattr(
        manageProject,
        "_loadSyncModule",
        lambda: SimpleNamespace(main=lambda: captured.extend(sys.argv)),
    )
    manageProject.main(["sync", "--repo", "owner/app", "--no-runtime"])
    assert captured == [
        "syncAgentInstructions.py",
        "--no-runtime",
        "--repo",
        "owner/app",
    ]


@pytest.mark.parametrize("path", ["output", "output/omprRuntimeBackups", "project"])
def testRemoteSymlinkParentsCannotBeReplacedByBackupTrees(path):
    snapshot = {"tree": [{"path": path, "mode": "120000", "type": "blob"}]}
    with pytest.raises(ValueError, match="requires review"):
        sync._runtimeUpdatesBuild("owner/app", "head", snapshot, {}, enabled=False)
