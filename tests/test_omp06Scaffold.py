"""Tests for OMP 0.6 package scaffold and managed-file relocation."""

import logging
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.managedContent import DEPLOYMENT_COMMENT
from organiseMyProjects.manageProject import createProject, updateProject


def testFootballVisionScaffoldUsesRootPackage(temp_dir):
    projectPath = temp_dir / "footballVision"
    with patch("organiseMyProjects.manageProject.subprocess.run"):
        createProject(str(projectPath))

    assert (projectPath / "footballVision" / "__init__.py").exists()
    assert not (projectPath / "src").exists()
    assert not (projectPath / "main.py").exists()
    assert (projectPath / "footballVisionEnvironment.yml").exists()
    assert (
        "pip install -e ."
        in (projectPath / "footballVisionEnvironment.yml").read_text()
        or "-e .[dev]" in (projectPath / "footballVisionEnvironment.yml").read_text()
    )
    pyproject = (projectPath / "pyproject.toml").read_text()
    assert 'packages = ["footballVision"]' in pyproject
    assert "[project.scripts]" not in pyproject
    assert (projectPath / "project" / "adr").is_dir()
    assert (projectPath / "project" / "requirements").is_dir()
    assert (projectPath / "project" / "reviews").is_dir()
    assert (projectPath / "documentation").is_dir()
    assert (projectPath / "tests").is_dir()
    assert not (projectPath / "omp").exists()

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "footballVisionGenerated",
        projectPath / "footballVision" / "__init__.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert (
        Path(module.__file__).resolve().parent
        == (projectPath / "footballVision").resolve()
    )


def testConfirmedRelocationRemovesObsoleteManagedFile(temp_dir, caplog):
    projectPath = temp_dir / "relocProject"
    projectPath.mkdir()
    githubDir = projectPath / ".github"
    githubDir.mkdir()
    legacy = githubDir / "repositoryLayout.md"
    legacy.write_text(DEPLOYMENT_COMMENT + "# old layout\n")

    with caplog.at_level(logging.INFO):
        updateProject(str(projectPath))

    dest = projectPath / "documentation" / "repositoryLayout.md"
    assert dest.exists()
    assert not legacy.exists()
    assert "removed obsolete managed file" in caplog.text
    assert "repositoryLayout.md" in dest.read_text()


def testDryRunRelocationDoesNotChangeFiles(temp_dir, caplog):
    projectPath = temp_dir / "relocDry"
    projectPath.mkdir()
    githubDir = projectPath / ".github"
    githubDir.mkdir()
    legacy = githubDir / "howToRelease.md"
    original = DEPLOYMENT_COMMENT + "# old release guide\n"
    legacy.write_text(original)

    with caplog.at_level(logging.INFO):
        updateProject(str(projectPath), dryRun=True)

    assert legacy.read_text() == original
    assert not (projectPath / "documentation" / "howToRelease.md").exists()
    assert "would remove obsolete managed file" in caplog.text
    assert "would create" in caplog.text or "would update" in caplog.text


def testAmbiguousLegacyFileIsPreserved(temp_dir, caplog):
    projectPath = temp_dir / "relocAmbiguous"
    projectPath.mkdir()
    githubDir = projectPath / ".github"
    githubDir.mkdir()
    legacy = githubDir / "requirementsManagement.md"
    legacy.write_text("# my local notes\n")

    with caplog.at_level(logging.INFO):
        updateProject(str(projectPath))

    assert legacy.exists()
    assert legacy.read_text() == "# my local notes\n"
    assert "ownership is ambiguous" in caplog.text
    assert (projectPath / "documentation" / "requirementsManagement.md").exists()


def testRelocationRerunIsIdempotent(temp_dir):
    projectPath = temp_dir / "relocAgain"
    projectPath.mkdir()
    githubDir = projectPath / ".github"
    githubDir.mkdir()
    (githubDir / "repositoryLayout.md").write_text(DEPLOYMENT_COMMENT + "# old\n")
    (githubDir / "requirementsManagement.md").write_text(DEPLOYMENT_COMMENT + "# old\n")
    (githubDir / "howToRelease.md").write_text(DEPLOYMENT_COMMENT + "# old\n")

    updateProject(str(projectPath))
    firstLayout = (projectPath / "documentation" / "repositoryLayout.md").read_text()
    updateProject(str(projectPath))

    assert (projectPath / "documentation" / "repositoryLayout.md").read_text() == (
        firstLayout
    )
    assert not (githubDir / "repositoryLayout.md").exists()
    assert not (githubDir / "requirementsManagement.md").exists()
    assert not (githubDir / "howToRelease.md").exists()


def testUpdateDoesNotCreateSrcOrMainForPackagedCli(temp_dir):
    projectPath = temp_dir / "packagedCli"
    package = projectPath / "packagedCli"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (projectPath / "pyproject.toml").write_text(
        '[project]\nname = "packagedCli"\n\n'
        '[project.scripts]\ntool = "packagedCli.cli:main"\n'
    )

    updateProject(str(projectPath))
    updateProject(str(projectPath))

    assert not (projectPath / "main.py").exists()
    assert not (projectPath / "src").exists()
