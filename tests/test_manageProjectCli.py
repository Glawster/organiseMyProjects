"""Tests for the manageProject console dispatcher."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from organiseMyProjects import manageProject, manageProjectCli
from organiseMyProjects.manageProject import commandArgvExpand


def testCommandArgvExpandRewritesLegacyFlags():
    assert commandArgvExpand(["--update", "-y"]) == ["update", "-y"]
    assert commandArgvExpand(["-u", "--confirm"]) == ["update", "--confirm"]
    assert commandArgvExpand(["--check"]) == ["check"]
    assert commandArgvExpand(["update", "-y"]) == ["update", "-y"]
    assert commandArgvExpand(["demoProject"]) == ["demoProject"]


def testCheckDefaultsToCurrentDirectory(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["manageProject", "check"])

    with patch(
        "organiseMyProjects.agentCheck.checkProject", return_value=0
    ) as checkProject:
        assert manageProjectCli.main() == 0

    checkProject.assert_called_once_with(tmp_path, strict=False, verbose=False)


def testCheckAcceptsProjectAndStrictVerbose(monkeypatch, tmp_path: Path):
    projectPath = tmp_path / "project"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manageProject",
            "check",
            "--project",
            str(projectPath),
            "--strict",
            "--verbose",
        ],
    )

    with patch(
        "organiseMyProjects.agentCheck.checkProject", return_value=1
    ) as checkProject:
        assert manageProjectCli.main() == 1

    checkProject.assert_called_once_with(projectPath, strict=True, verbose=True)


def testCheckAcceptsLegacyProjectOption(monkeypatch, tmp_path: Path):
    projectPath = tmp_path / "project"
    monkeypatch.setattr(
        sys,
        "argv",
        ["manageProject", "check", "--project", str(projectPath)],
    )

    with patch(
        "organiseMyProjects.agentCheck.checkProject", return_value=0
    ) as checkProject:
        assert manageProjectCli.main() == 0

    checkProject.assert_called_once_with(projectPath, strict=False, verbose=False)


def testCheckRejectsUpdateCommand(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["manageProject", "check", "--update"])

    with pytest.raises(SystemExit) as excInfo:
        manageProjectCli.main()

    assert excInfo.value.code == 2


def testLegacyCheckFlagStillWorks(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["manageProject", "--check"])

    with patch(
        "organiseMyProjects.agentCheck.checkProject", return_value=0
    ) as checkProject:
        assert manageProjectCli.main() == 0

    checkProject.assert_called_once_with(tmp_path, strict=False, verbose=False)


def testUpdateCommandDoesNotCreateAProjectNamedUpdate(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["manageProject", "update", "-y"])

    with patch.object(manageProject, "updateProject") as updateProject:
        with patch.object(manageProject, "createProject") as createProject:
            assert manageProjectCli.main() == 0

    createProject.assert_not_called()
    updateProject.assert_called_once()
    assert updateProject.call_args.args[0] == tmp_path
    assert not (tmp_path / "update").exists()


def testUpdateAcceptsProjectFlag(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["manageProject", "update", "--project", "demo", "-y"]
    )

    with patch.object(manageProject, "updateProject") as updateProject:
        assert manageProjectCli.main() == 0

    updateProject.assert_called_once()
    assert updateProject.call_args.args[0] == "demo"


def testUpdateAcceptsProjectFlagBeforeCommand(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["manageProject", "--project", "demo", "update", "-y"]
    )

    with patch.object(manageProject, "updateProject") as updateProject:
        assert manageProjectCli.main() == 0

    updateProject.assert_called_once()
    assert updateProject.call_args.args[0] == "demo"


def testCreateAcceptsProjectFlag(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        sys, "argv", ["manageProject", "create", "--project", "demo", "-y"]
    )

    with patch.object(manageProject, "createProject") as createProject:
        assert manageProjectCli.main() == 0

    createProject.assert_called_once_with(
        "demo",
        dryRun=False,
        includeUi=False,
        includeQt=False,
    )


def testCreateRequiresProjectOption(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["manageProject", "create", "-y"])

    with patch.object(manageProject, "createProject") as createProject:
        with pytest.raises(SystemExit) as excInfo:
            manageProjectCli.main()

    createProject.assert_not_called()
    assert excInfo.value.code == 2


def testUnknownCommandIsRejected(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["manageProject", "mystery", "-y"])

    with patch.object(manageProject, "createProject") as createProject:
        with pytest.raises(SystemExit) as excInfo:
            manageProjectCli.main()

    createProject.assert_not_called()
    assert excInfo.value.code == 2
    assert not (tmp_path / "mystery").exists()
