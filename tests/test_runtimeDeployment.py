"""Production and failure-path evidence for deployed OMPR runtime helpers."""

import base64
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import syncAgentInstructions as sync
from organiseMyProjects import manageProject
from organiseMyProjects.managedContent import managedContentBuild
from organiseMyProjects.runtimeDeployment import (
    runtimeDeploy,
    runtimeFiles,
    runtimeMigrationReport,
)
from organiseMyProjects.version import VERSION


@pytest.fixture
def application(tmp_path):
    """Create a real scaffold while suppressing Git/pre-commit side effects."""
    root = tmp_path / "sampleApp"
    with patch.object(manageProject.subprocess, "run"):
        manageProject.createProject(root)
    # Exercise the actual generated entry-point template without optional UI.
    (root / "sampleApp" / "__main__.py").write_text(manageProject.PACKAGE_MAIN_CONTENT)
    return root


def testIndependentApplicationAndWheel(application, tmp_path):
    """Build/install the scaffold and run its entry point without OMPR or site packages."""
    pytest.importorskip("build", reason="build is required for distribution evidence")
    pytest.importorskip(
        "setuptools", reason="setuptools is required for distribution evidence"
    )
    pytest.importorskip("wheel", reason="wheel is required for distribution evidence")
    distribution = tmp_path / "dist"
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
        cwd=application,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(distribution.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        assert {
            "ompr/__init__.py",
            "ompr/logUtils.py",
            "ompr/logUtils.sh",
            "ompr/version.py",
        } <= set(archive.namelist())
        metadata = archive.read(
            next(
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/METADATA")
            )
        ).decode()
        assert "Requires-Dist: organiseMyProjects" not in metadata
    installed = tmp_path / "installed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-index",
            "--target",
            str(installed),
            str(wheel),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    for path in (application, installed):
        script = """
import importlib.abc
import pathlib
import runpy
import sys
sys.path.insert(0, sys.argv[1])
class RejectTooling(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'organiseMyProjects':
            raise AssertionError('application imported OMPR tooling')
sys.meta_path.insert(0, RejectTooling())
from ompr.logUtils import getLogger, setApplication
from ompr.version import VERSION
setApplication('independent', logDir=pathlib.Path(sys.argv[2]))
logger = getLogger()
logger.info('independent runtime works')
assert VERSION
assert not any(name.startswith('organiseMyProjects') for name in sys.modules)
sys.argv = ['sampleApp', '--help']
runpy.run_module('sampleApp', run_name='__main__')
"""
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                "-c",
                script,
                str(path),
                str(tmp_path / "logs"),
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        assert "--confirm" in completed.stdout
    assert (
        "independent runtime works"
        in next((tmp_path / "logs").glob("*.log")).read_text()
    )
    completed = subprocess.run(
        [
            "bash",
            "-c",
            'set -euo pipefail; source "$1/ompr/logUtils.sh"; setApplication shell "$2"; log_info "shell works"',
            "bash",
            str(installed),
            str(tmp_path / "shellLogs"),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "shell works" in completed.stdout


def testManagedOverwriteModesAndIdempotence(application):
    """Modified managed files refresh; an identical second deployment does no writes."""
    helper = application / "ompr" / "logUtils.py"
    helper.write_text(helper.read_text() + "\n# local modification\n")
    runtimeDeploy(application, dryRun=False, logger=MagicMock())
    assert "local modification" not in helper.read_text()
    # Metadata from an older deployment does not itself cause a rewrite.
    helper.write_text(helper.read_text().replace(f"release {VERSION}", "release 0.1"))
    for source, relative in runtimeFiles():
        deployed = application / relative
        assert manageProject.ownershipPolicy(relative) == "managed-overwrite"
        assert deployed.stat().st_mode & 0o111 == source.stat().st_mode & 0o111
        assert "Glawster/organiseMyProjects release" in deployed.read_text()
    snapshot = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (application / "ompr").iterdir()
    }
    runtimeDeploy(application, dryRun=False, logger=MagicMock())
    assert snapshot == {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in snapshot
    }


def testDryRunAndCollisionProtection(application, tmp_path):
    """Dry runs preserve bytes; collisions and symlinks fail before runtime writes."""
    helper = application / "ompr" / "logUtils.py"
    helper.write_text(helper.read_text() + "\n# pending\n")
    previous = helper.read_bytes()
    runtimeDeploy(application, dryRun=True, logger=MagicMock())
    assert helper.read_bytes() == previous
    empty = tmp_path / "empty"
    runtimeDeploy(empty, dryRun=True, logger=MagicMock())
    assert not empty.exists()
    helper.write_text("# project owned\n")
    with pytest.raises(ValueError, match="project-owned runtime"):
        runtimeDeploy(application, dryRun=False, logger=MagicMock())
    assert helper.read_text() == "# project owned\n"
    helper.unlink()
    external = tmp_path / "external.py"
    external.write_text("# external\n")
    helper.symlink_to(external)
    with pytest.raises(ValueError, match="requires review"):
        runtimeDeploy(application, dryRun=False, logger=MagicMock())
    assert external.read_text() == "# external\n"


def testUnownedPackageAndSymlinkDirectoryPreserved(tmp_path):
    root = tmp_path / "consumer"
    package = root / "ompr"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("# user package\n")
    with pytest.raises(ValueError, match="project-owned ompr"):
        runtimeDeploy(root, dryRun=False, logger=MagicMock())
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "ompr").symlink_to(package, target_is_directory=True)
    with pytest.raises(ValueError, match="not a regular directory"):
        runtimeDeploy(linked, dryRun=False, logger=MagicMock())
    assert list(package.iterdir()) == [package / "__init__.py"]


def testExistingMigrationReportsWithoutEditing(application):
    """Ordinary update reports imports and packaging while preserving user files."""
    legacy = application / "sampleApp" / "legacy.py"
    legacy.write_text("from organiseMyProjects.logUtils import getLogger\n")
    original = legacy.read_bytes()
    metadata = (application / "pyproject.toml").read_bytes()
    logger = MagicMock()
    runtimeMigrationReport(application, logger)
    assert any("legacy.py" in call.args[0] for call in logger.warning.call_args_list)
    assert any(
        "packaging review" in call.args[0] for call in logger.warning.call_args_list
    )
    manageProject.updateProject(application)
    assert legacy.read_bytes() == original
    assert (application / "pyproject.toml").read_bytes() == metadata


def testCanonicalSourceAndReservedName(tmp_path):
    source = Path(manageProject.__file__).parent
    previous = (source / "logUtils.py").read_bytes()
    manageProject.updateProject(source.parent)
    assert not (source.parent / "ompr").exists()
    assert (source / "logUtils.py").read_bytes() == previous
    with pytest.raises(ValueError, match="canonical runtime"):
        runtimeDeploy(source.parent, dryRun=False, logger=MagicMock())
    with pytest.raises(ValueError, match="reserved"):
        manageProject.createProject(tmp_path / "ompr")


def _syncFixture(monkeypatch, entries=None, contents=None):
    """Substitute only HTTP boundaries; retain real sync composition and manifest."""
    monkeypatch.setattr(sync, "getDefaultBranch", lambda *args: "main")
    branches = {"main": "head"}

    def branchHead(repo, branch, headers):
        if branch not in branches:
            response = sync.requests.Response()
            response.status_code = 404
            raise sync.requests.HTTPError(response=response)
        return branches[branch]

    monkeypatch.setattr(sync, "getBranchHeadSha", branchHead)
    monkeypatch.setattr(
        sync,
        "createBranch",
        MagicMock(
            side_effect=lambda repo, branch, head, headers: branches.setdefault(
                branch, head
            )
        ),
    )
    monkeypatch.setattr(
        sync,
        "getRemoteFile",
        lambda repo, path, headers, ref: {
            "content": base64.b64encode(contents[path].encode()).decode()
        },
    )
    response = MagicMock()
    response.json.return_value = {"sha": "tree", "tree": entries or []}
    get = MagicMock(return_value=response)
    post = MagicMock(return_value=response)
    patchRef = MagicMock(return_value=response)
    monkeypatch.setattr(sync.requests, "get", get)
    monkeypatch.setattr(sync.requests, "post", post)
    monkeypatch.setattr(sync.requests, "patch", patchRef)
    return get, post, patchRef


def testRuntimeSyncAtomicTreeAndModes(monkeypatch, tmp_path):
    """All selected runtime contents and modes land in a single tree commit."""
    _get, post, patchRef = _syncFixture(monkeypatch)
    prepared = set()
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), prepared)
        == "updated"
    )
    payload = post.call_args_list[0].kwargs["json"]
    assert payload["base_tree"] == "tree"
    assert {entry["path"] for entry in payload["tree"]} == {
        path.as_posix() for _, path in runtimeFiles()
    }
    for entry in payload["tree"]:
        assert entry["mode"] in {"100644", "100755"}
        assert "# synced from Glawster/organiseMyProjects release" in entry["content"]
        if entry["path"].endswith(".sh"):
            assert entry["content"].startswith("#!/usr/bin/env bash\n# synced")
    assert len(post.call_args_list) == 2
    assert patchRef.call_args.kwargs["json"]["force"] is False
    assert prepared == {"owner/app"}


def testRuntimeSyncDryRunIdempotenceAndOwnership(monkeypatch):
    _get, post, patchRef = _syncFixture(monkeypatch)
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", True, {}, MagicMock(), set())
        == "updated"
    )
    post.assert_not_called()
    patchRef.assert_not_called()
    sync.createBranch.assert_not_called()
    entries = []
    contents = {}
    for source, relative in runtimeFiles():
        path = relative.as_posix()
        contents[path] = managedContentBuild(source.read_text(), suffix=source.suffix)
        entries.append(
            {
                "path": path,
                "type": "blob",
                "mode": "100755" if source.stat().st_mode & 0o111 else "100644",
            }
        )
    _get, post, patchRef = _syncFixture(monkeypatch, entries, contents)
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "skipped"
    )
    post.assert_not_called()
    contents["ompr/logUtils.py"] = "# user owned\n"
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "failed"
    )
    post.assert_not_called()
    entries[1]["mode"] = "120000"
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "failed"
    )
    patchRef.assert_not_called()


def testRuntimeSyncFailureDoesNotAdvanceRef(monkeypatch):
    _get, post, patchRef = _syncFixture(monkeypatch)
    post.return_value.raise_for_status.side_effect = sync.requests.HTTPError(
        "test failure"
    )
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "failed"
    )
    patchRef.assert_not_called()


def testRemoteCanonicalSourceIsProtected(monkeypatch):
    get, post, patchRef = _syncFixture(monkeypatch)
    assert (
        sync.runtimeSyncRepo(
            sync.SOURCE_REPO, "sync/test", False, {}, MagicMock(), set()
        )
        == "failed"
    )
    get.assert_not_called()
    post.assert_not_called()
    patchRef.assert_not_called()


def testRuntimeSyncReadsExistingBranchSnapshot(monkeypatch):
    """A retry uses the existing sync branch, even when no instructions changed."""
    get, post, _patchRef = _syncFixture(monkeypatch)
    sync.createBranch("owner/app", "sync/test", "branch-head", {})
    sync.createBranch.reset_mock()
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "updated"
    )
    assert get.call_args.args[0].endswith("/git/trees/branch-head")
    assert post.call_args_list[1].kwargs["json"]["parents"] == ["branch-head"]
    sync.createBranch.assert_not_called()


def testManifestExtensionAndExecutableMode(monkeypatch, application):
    """Adding one approved helper extends local and remote deployment together."""
    import organiseMyProjects.runtimeDeployment as runtime

    helper = application.parent / "helper.sh"
    helper.write_text("#!/usr/bin/env bash\nprintf 'helper works\\n'\n")
    helper.chmod(0o755)
    files = runtimeFiles() + [(helper, Path("ompr/helper.sh"))]
    monkeypatch.setattr(runtime, "runtimeFiles", lambda: files)
    monkeypatch.setattr(sync, "runtimeFiles", lambda: files)
    runtimeDeploy(application, dryRun=False, logger=MagicMock())
    assert (application / "ompr/helper.sh").stat().st_mode & 0o111 == 0o111
    (application / "ompr/helper.sh").chmod(0o644)
    runtimeDeploy(application, dryRun=False, logger=MagicMock())
    assert (application / "ompr/helper.sh").stat().st_mode & 0o111 == 0o111
    _get, post, _patchRef = _syncFixture(monkeypatch)
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "updated"
    )
    entry = next(
        item
        for item in post.call_args_list[0].kwargs["json"]["tree"]
        if item["path"] == "ompr/helper.sh"
    )
    assert entry["mode"] == "100755"
    assert entry["content"].startswith("#!/usr/bin/env bash\n# synced")


def testRuntimeCliForwardingAndUiPackaging(monkeypatch):
    """The public management command forwards runtime selection to sync."""
    import types

    observed = []
    monkeypatch.setattr(
        manageProject,
        "_loadSyncModule",
        lambda: types.SimpleNamespace(main=lambda: observed.extend(sys.argv)),
    )
    manageProject.main(["sync", "--repo", "owner/app", "--runtime"])
    assert observed == ["syncAgentInstructions.py", "--runtime", "--repo", "owner/app"]
    metadata = manageProject._pyprojectContentBuild(
        "app", includeUi=True, includeQt=True
    )
    assert 'packages = ["app", "ompr", "app.ui", "app.qt"]' in metadata
    assert 'ompr = ["*.sh"]' in metadata


def testRuntimeSyncFailurePreventsMerge(monkeypatch):
    """The public sync loop does not merge a repository whose runtime failed."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "syncAgentInstructions.py",
            "--runtime",
            "--merge",
            "--confirm",
            "--repo",
            "owner/app",
        ],
    )
    monkeypatch.setattr(sync, "configLoadToken", lambda: "test-token")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(sync, "getTargetRepos", lambda headers: ["owner/app"])
    monkeypatch.setattr(sync, "syncRepo", lambda *args, **kwargs: "ready")
    monkeypatch.setattr(sync, "runtimeSyncRepo", lambda *args, **kwargs: "failed")
    merge = MagicMock()
    monkeypatch.setattr(sync, "syncPullRequest", merge)
    sync.main()
    merge.assert_not_called()


@pytest.mark.parametrize(
    "entries",
    [
        [{"path": "ompr", "type": "blob", "mode": "120000"}],
        [{"path": "ompr/unrelated.py", "type": "blob", "mode": "100644"}],
    ],
)
def testRemoteUnownedPathsArePreserved(monkeypatch, entries):
    _get, post, patchRef = _syncFixture(monkeypatch, entries)
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "failed"
    )
    post.assert_not_called()
    patchRef.assert_not_called()


def testRemoteTruncatedTreeIsNotWritten(monkeypatch):
    get, post, patchRef = _syncFixture(monkeypatch)
    get.return_value.json.return_value["truncated"] = True
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "failed"
    )
    post.assert_not_called()
    patchRef.assert_not_called()


def testManagedRemoteModificationRefreshesOnlyChangedFile(monkeypatch):
    entries = []
    contents = {}
    for source, relative in runtimeFiles():
        path = relative.as_posix()
        contents[path] = managedContentBuild(source.read_text(), suffix=source.suffix)
        entries.append(
            {
                "path": path,
                "type": "blob",
                "mode": "100755" if source.stat().st_mode & 0o111 else "100644",
            }
        )
    contents["ompr/logUtils.py"] += "\n# modified deployed logger\n"
    _get, post, _patchRef = _syncFixture(monkeypatch, entries, contents)
    assert (
        sync.runtimeSyncRepo("owner/app", "sync/test", False, {}, MagicMock(), set())
        == "updated"
    )
    updates = post.call_args_list[0].kwargs["json"]["tree"]
    assert [entry["path"] for entry in updates] == ["ompr/logUtils.py"]
    assert "modified deployed logger" not in updates[0]["content"]
