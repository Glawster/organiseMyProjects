"""Tests for the manageProject console dispatcher."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from organiseMyProjects import manageProjectCli


def testCheckDefaultsToCurrentDirectory(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["manageProject", "--check"])

    with patch.object(manageProjectCli, "checkProject", return_value=0) as checkProject:
        assert manageProjectCli.main() == 0

    checkProject.assert_called_once_with(tmp_path, strict=False, verbose=False)


def testCheckAcceptsProjectAndStrictVerbose(monkeypatch, tmp_path: Path):
    projectPath = tmp_path / "project"
    monkeypatch.setattr(
        sys,
        "argv",
        ["manageProject", "--check", str(projectPath), "--strict", "--verbose"],
    )

    with patch.object(manageProjectCli, "checkProject", return_value=1) as checkProject:
        assert manageProjectCli.main() == 1

    checkProject.assert_called_once_with(projectPath, strict=True, verbose=True)


def testCheckAcceptsLegacyProjectOption(monkeypatch, tmp_path: Path):
    projectPath = tmp_path / "project"
    monkeypatch.setattr(
        sys,
        "argv",
        ["manageProject", "--check", "--project", str(projectPath)],
    )

    with patch.object(manageProjectCli, "checkProject", return_value=0) as checkProject:
        assert manageProjectCli.main() == 0

    checkProject.assert_called_once_with(projectPath, strict=False, verbose=False)


def testCheckRejectsUpdateMode(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["manageProject", "--check", "--update"])

    with pytest.raises(SystemExit) as excInfo:
        manageProjectCli.main()

    assert excInfo.value.code == 2


def testNonCheckDelegatesToExistingManageProject(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["manageProject", "demoProject", "--update"])
    delegatedMain = Mock(return_value=None)

    with patch.object(manageProjectCli.manageProject, "main", delegatedMain):
        assert manageProjectCli.main() == 0

    delegatedMain.assert_called_once_with()
