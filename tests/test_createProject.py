"""
Tests for manageProject.py functionality.
"""

import logging
import pytest
import os
import sys
import types
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.manageProject import (
    createProject,
    updateProject,
    main as createProjectMain,
    _copy_if_newer,
    _update_text_file,
    _build_managed_content,
    DEPLOYMENT_COMMENT,
    PYTHON_DEPLOYMENT_COMMENT,
    GITIGNORE_CONTENT,
    REQUIREMENTS_CONTENT,
    DEV_REQUIREMENTS_CONTENT,
    MAIN_PY_CONTENT,
    PRECOMMIT_CONTENT,
    PYTEST_INI_CONTENT,
    VSCODE_SETTINGS_CONTENT,
)


def assert_no_gui_scaffolds(projectPath: Path):
    assert not (projectPath / "ui").exists()
    assert not (projectPath / "qt").exists()


class TestCreateProject:
    """Test cases for createProject function."""

    def testCreateProjectBasicStructure(self, temp_dir, sample_project_name):
        """Test that createProject creates the basic directory structure."""
        projectPath = temp_dir / sample_project_name

        # Mock subprocess to avoid git/pre-commit dependencies
        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        # Verify directory structure
        assert projectPath.exists()
        assert (projectPath / "src").exists()
        assert (projectPath / "tests").exists()
        assert (projectPath / "logs").exists()
        assert (projectPath / ".github").exists()

        # Verify package init files
        assert (projectPath / "src" / "__init__.py").exists()
        assert_no_gui_scaffolds(projectPath)

    def testCreateProjectCoreFiles(self, temp_dir, sample_project_name):
        """Test that createProject creates core configuration files."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        # Verify core files exist
        assert (projectPath / ".gitignore").exists()
        assert (projectPath / "requirements.txt").exists()
        assert (projectPath / "dev-requirements.txt").exists()
        assert (projectPath / "README.md").exists()
        assert (projectPath / "main.py").exists()
        assert (projectPath / ".pre-commit-config.yaml").exists()

    def testCreateProjectFileContents(self, temp_dir, sample_project_name):
        """Test that createProject creates files with correct content."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        # Verify file contents
        assert (projectPath / ".gitignore").read_text() == GITIGNORE_CONTENT
        assert (projectPath / "requirements.txt").read_text() == REQUIREMENTS_CONTENT
        assert (
            projectPath / "dev-requirements.txt"
        ).read_text() == DEV_REQUIREMENTS_CONTENT
        assert (projectPath / "main.py").read_text() == MAIN_PY_CONTENT
        assert (
            projectPath / ".pre-commit-config.yaml"
        ).read_text() == PRECOMMIT_CONTENT

        # Verify README content
        readmeContent = (projectPath / "README.md").read_text()
        assert sample_project_name in readmeContent
        assert "Project scaffold created by manageProject.py" in readmeContent

    def testCreateProjectPytestIni(self, temp_dir, sample_project_name):
        """Test that createProject creates pytest.ini with the correct content."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        assert (projectPath / "pytest.ini").exists()
        assert (projectPath / "pytest.ini").read_text() == PYTEST_INI_CONTENT

    def testCreateProjectVscodeSettings(self, temp_dir, sample_project_name):
        """Test that createProject creates .vscode/settings.json with the correct content."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        assert (projectPath / ".vscode" / "settings.json").exists()
        assert (
            projectPath / ".vscode" / "settings.json"
        ).read_text() == VSCODE_SETTINGS_CONTENT

    def testCreateProjectTemplateFiles(self, temp_dir, sample_project_name):
        """Test that only non-UI template files are copied by default."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        # Verify template files are copied
        assert (
            projectPath / "src" / "globalVars.py"
        ).exists(), "globalVars.py should be copied to new projects"
        assert (projectPath / "tests" / "runLinter.py").exists()
        assert (projectPath / "tests" / "guiNamingLinter.py").exists()
        assert_no_gui_scaffolds(projectPath)

        # Verify package utilities are NOT copied
        assert not (
            projectPath / "src" / "logUtils.py"
        ).exists(), "logUtils.py should NOT be copied to new projects"
        assert not (
            projectPath / "manageProject.py"
        ).exists(), "manageProject.py should NOT be copied to new projects"

    def testCreateProjectUiTemplates(self, temp_dir, sample_project_name):
        """Test that tkinter UI templates are copied only when requested."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath), includeUi=True)

        assert (projectPath / "ui" / "__init__.py").exists()
        assert (projectPath / "ui" / "styleUtils.py").exists()
        assert (projectPath / "ui" / "mainMenu.py").exists()
        assert (projectPath / "ui" / "baseFrame.py").exists()
        assert (projectPath / "ui" / "frameTemplate.py").exists()
        assert (projectPath / "ui" / "statusFrame.py").exists()

    def testCreateProjectQtTemplates(self, temp_dir, sample_project_name):
        """Test that Qt templates are copied only when requested."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath), includeQt=True)

        assert (projectPath / "qt" / "__init__.py").exists()
        assert (projectPath / "qt" / "styleUtils.py").exists()
        assert (projectPath / "qt" / "mainMenu.py").exists()
        assert (projectPath / "qt" / "baseFrame.py").exists()
        assert (projectPath / "qt" / "frameTemplate.py").exists()
        assert (projectPath / "qt" / "statusFrame.py").exists()

    def testCreateProjectAlreadyExists(self, temp_dir, sample_project_name, caplog):
        """Test behavior when project directory already exists."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()  # Create directory first

        with caplog.at_level(logging.INFO):
            createProject(str(projectPath))

        assert "already exists" in caplog.text

    def testCreateProjectAgentGuidelines(self, temp_dir, sample_project_name):
        """Test that agent guidelines are copied from the .github/ directory."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        agentGuidelines = projectPath / ".github" / "agent-instructions.md"
        copilotGuidelines = projectPath / ".github" / "copilot-instructions.md"
        claudeGuidelines = projectPath / "CLAUDE.md"
        assert agentGuidelines.exists()
        assert len(agentGuidelines.read_text()) > 0
        assert copilotGuidelines.exists()
        assert "agent-instructions.md" in copilotGuidelines.read_text()
        assert "repositoryLayout.md" not in copilotGuidelines.read_text()
        assert claudeGuidelines.exists()
        assert "agent-instructions.md" in claudeGuidelines.read_text()
        assert "repositoryLayout.md" not in claudeGuidelines.read_text()
        assert agentGuidelines.read_text().startswith(DEPLOYMENT_COMMENT)

    def testCreateProjectAgentInstructions(self, temp_dir, sample_project_name):
        """Test that Codex agent instructions are copied to the project root."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        agentFile = projectPath / "AGENTS.md"
        sourceFile = Path(__file__).parent.parent / ".github" / "AGENTS.md"
        assert agentFile.read_text() == _build_managed_content(sourceFile.read_text())
        assert "repositoryLayout.md" not in agentFile.read_text()

    def testCreateProjectRepositoryLayout(self, temp_dir, sample_project_name):
        """Test that the shared repository layout is project documentation."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        layoutFile = projectPath / "documentation" / "repositoryLayout.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "repositoryLayout.md"
        )
        assert layoutFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testCreateProjectRequirementsManagement(self, temp_dir, sample_project_name):
        """Test that the shared requirements guide is project documentation."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        guideFile = projectPath / "documentation" / "requirementsManagement.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "requirementsManagement.md"
        )
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())
        assert (
            "Read `documentation/requirementsManagement.md`."
            in (projectPath / ".github" / "agent-instructions.md").read_text()
        )

    def testCreateProjectTestingProcess(self, temp_dir, sample_project_name):
        """Test that new projects receive the authoritative testing process."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        guideFile = projectPath / "documentation" / "testingProcess.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "testingProcess.md"
        )
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())
        readmeText = (projectPath / "README.md").read_text()
        assert "documentation/repositoryLayout.md" in readmeText
        assert "documentation/requirementsManagement.md" in readmeText
        assert "documentation/testingProcess.md" in readmeText

    def testCreateProjectHowToRelease(self, temp_dir, sample_project_name):
        """Test that the shared release guide is project documentation."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        guideFile = projectPath / "documentation" / "howToRelease.md"
        sourceFile = Path(__file__).parent.parent / "documentation" / "howToRelease.md"
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testCreateProjectAgentPortabilityStructure(self, temp_dir, sample_project_name):
        """Test that project creation scaffolds architecture, currentIncrement, project.yaml, and roadmap."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        assert (projectPath / "documentation" / "architecture.md").exists()
        assert (projectPath / "project" / "currentIncrement.md").exists()
        incrementText = (
            projectPath / "project" / "currentIncrement.md"
        ).read_text()
        assert "## Increment" in incrementText
        assert "## Requirement" in incrementText
        assert "## Verification" in incrementText
        assert "## Next" in incrementText
        assert "## In-Progress Tasks" not in incrementText
        assert "## Handoff & Unresolved Context" not in incrementText
        assert (projectPath / "project" / "project.yaml").exists()
        assert (projectPath / "project" / "roadmap.md").exists()
        assert (projectPath / "project" / "requirements" / "README.md").exists()
        assert (
            projectPath / "project" / "requirements" / "templates" / "requirement.md"
        ).exists()
        requirementText = (
            projectPath
            / "project"
            / "requirements"
            / "templates"
            / "requirement.md"
        ).read_text()
        assert "## Traceability" not in requirementText
        assert (projectPath / "project" / "adr" / "README.md").exists()
        assert (projectPath / "project" / "adr" / "templates" / "adr.md").exists()


class TestUpdateProject:
    """Test cases for updateProject function."""

    def testUpdateProjectExisting(self, temp_dir, sample_project_name):
        """Test updating an existing project without scaffold growth."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        # Verify only managed metadata folders are created by default
        assert (projectPath / ".github").exists()
        assert not (projectPath / "src").exists()
        # Managed test helper files are still deployed under tests/
        assert (projectPath / "tests").exists()
        assert not (projectPath / "logs").exists()
        assert_no_gui_scaffolds(projectPath)

    def testUpdateProjectNonexistent(self, temp_dir, sample_project_name, caplog):
        """Test behavior when trying to update non-existent project."""
        projectPath = temp_dir / sample_project_name

        with caplog.at_level(logging.INFO):
            updateProject(str(projectPath))

        assert "does not exist" in caplog.text

    def testUpdateProjectPytestIni(self, temp_dir, sample_project_name):
        """Test that updateProject creates/updates pytest.ini with the correct content."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / "pytest.ini").exists()
        assert (projectPath / "pytest.ini").read_text() == PYTEST_INI_CONTENT

    def testUpdateProjectVscodeSettings(self, temp_dir, sample_project_name):
        """Test that updateProject creates/updates .vscode/settings.json with the correct content."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / ".vscode" / "settings.json").exists()
        assert (
            projectPath / ".vscode" / "settings.json"
        ).read_text() == VSCODE_SETTINGS_CONTENT

    def testUpdateProjectAddsAgentInstructions(self, temp_dir, sample_project_name):
        """Test that updateProject adds managed Codex agent instructions."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        updateProject(str(projectPath))

        agentFile = projectPath / "AGENTS.md"
        sourceFile = Path(__file__).parent.parent / ".github" / "AGENTS.md"
        assert agentFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testUpdateProjectAddsRepositoryLayout(self, temp_dir, sample_project_name):
        """Test that updateProject adds the managed repository layout."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        updateProject(str(projectPath))

        layoutFile = projectPath / "documentation" / "repositoryLayout.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "repositoryLayout.md"
        )
        assert layoutFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testUpdateProjectAddsRequirementsManagement(
        self, temp_dir, sample_project_name
    ):
        """Test that updateProject adds the managed requirements guide."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        updateProject(str(projectPath))

        guideFile = projectPath / "documentation" / "requirementsManagement.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "requirementsManagement.md"
        )
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testUpdateProjectMigratesUnambiguousLegacyNames(
        self, temp_dir, sample_project_name
    ):
        """Migrate legacy OMP names without overwriting arbitrary targets."""
        projectPath = temp_dir / sample_project_name
        testsPath = projectPath / "tests"
        featuresPath = projectPath / "project" / "requirements" / "features"
        promptsPath = projectPath / "project" / "requirements" / "prompt"
        testsPath.mkdir(parents=True)
        featuresPath.mkdir(parents=True)
        promptsPath.mkdir(parents=True)
        (testsPath / "test_FooBar.py").write_text("def test_example(): pass\n")
        (featuresPath / "007-roleAssessment.md").write_text("# 007: Role assessment\n")
        (promptsPath / "007-roleAssessment.prompt.md").write_text("# Prompt\n")
        requirementsIndex = projectPath / "project" / "requirements" / "README.md"
        requirementsIndex.write_text(
            "# Requirements\n\n[Prompt](prompt/007-roleAssessment.prompt.md)\n"
        )

        updateProject(str(projectPath))

        assert (testsPath / "test_fooBar.py").exists()
        assert not (testsPath / "test_FooBar.py").exists()
        assert (promptsPath / "007-roleAssessment.md").exists()
        assert "prompt/007-roleAssessment.md" in requirementsIndex.read_text()

    def testUpdateProjectAddsHowToRelease(self, temp_dir, sample_project_name):
        """Test that updateProject adds the managed release process guide."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        updateProject(str(projectPath))

        guideFile = projectPath / "documentation" / "howToRelease.md"
        sourceFile = Path(__file__).parent.parent / "documentation" / "howToRelease.md"
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testUpdateProjectPytestIniOutdated(self, temp_dir, sample_project_name):
        """Test that updateProject updates pytest.ini if it is outdated."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        (projectPath / "pytest.ini").write_text("old content")

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / "pytest.ini").read_text() == PYTEST_INI_CONTENT

    def testUpdateProjectVscodeSettingsOutdated(self, temp_dir, sample_project_name):
        """Test that updateProject updates .vscode/settings.json if it is outdated."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        (projectPath / ".vscode").mkdir()
        (projectPath / ".vscode" / "settings.json").write_text('{"old": true}')

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (
            projectPath / ".vscode" / "settings.json"
        ).read_text() == VSCODE_SETTINGS_CONTENT

    def testUpdateProjectPreservesExistingUiTemplates(
        self, temp_dir, sample_project_name
    ):
        """Test that updateProject does not modify project-owned tkinter scaffolds."""
        projectPath = temp_dir / sample_project_name
        (projectPath / "ui").mkdir(parents=True)
        customMainMenu = "print('custom ui')\n"
        (projectPath / "ui" / "mainMenu.py").write_text(customMainMenu)

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / "ui" / "mainMenu.py").read_text() == customMainMenu
        assert not (projectPath / "ui" / "statusFrame.py").exists()

    def testUpdateProjectPreservesExistingMainPy(self, temp_dir, sample_project_name):
        """Test that updateProject does not overwrite project-owned main.py code."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        customMain = "print('custom main')\n"
        (projectPath / "main.py").write_text(customMain)

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / "main.py").read_text() == customMain


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def testBuildManagedPythonContentPreservesShebang(self):
        """Python deployment comments must follow the interpreter directive."""
        source = '#!/usr/bin/env python3\n"""CLI entry point."""\n'

        content = _build_managed_content(source, suffix=".py")

        assert content == (
            "#!/usr/bin/env python3\n"
            + PYTHON_DEPLOYMENT_COMMENT
            + '"""CLI entry point."""\n'
        )
        compile(content, "runLinter.py", "exec")

    def testCopyIfNewerNewFile(self, temp_dir):
        """Test copying when destination doesn't exist."""
        src = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"

        src.write_text("test content")

        _copy_if_newer(src, dest)

        assert dest.exists()
        assert dest.read_text() == "test content"

    def testCopyIfNewerOlderDest(self, temp_dir):
        """Test copying when source is newer than destination."""
        import time

        src = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"

        # Create dest first (older)
        dest.write_text("old content")

        # Wait a bit to ensure different modification times
        time.sleep(0.1)

        # Create src after (newer)
        src.write_text("new content")

        _copy_if_newer(src, dest)

        assert dest.read_text() == "new content"

    def testUpdateTextFileNew(self, temp_dir):
        """Test updating text file when it doesn't exist."""
        dest = temp_dir / "test.txt"
        content = "test content"

        _update_text_file(dest, content)

        assert dest.exists()
        assert dest.read_text() == content

    def testUpdateTextFileSameContent(self, temp_dir):
        """Test updating text file when content is the same."""
        dest = temp_dir / "test.txt"
        content = "test content"

        dest.write_text(content)
        originalMtime = dest.stat().st_mtime

        _update_text_file(dest, content)

        # File should not be modified if content is the same
        assert dest.stat().st_mtime == originalMtime

    def testUpdateTextFileDifferentContent(self, temp_dir):
        """Test updating text file when content is different."""
        dest = temp_dir / "test.txt"
        oldContent = "old content"
        newContent = "new content"

        dest.write_text(oldContent)

        _update_text_file(dest, newContent)

        assert dest.read_text() == newContent


class TestUpdateHelpers:
    """Test helper behavior used during project updates."""

    def testCopyIfNewerOverwritesWithoutBackup(self, temp_dir):
        """Test that _copy_if_newer updates in place without creating backup files."""
        import time

        src = temp_dir / "source.py"
        dest = temp_dir / "dest.py"

        dest.write_text("old content")
        time.sleep(0.05)
        src.write_text("new content")

        _copy_if_newer(src, dest)

        assert dest.read_text() == "new content"
        assert list(temp_dir.glob("dest.*.py")) == []

    def testUpdateTextFileOverwritesWithoutBackup(self, temp_dir):
        """Test that _update_text_file updates in place without creating backup files."""
        dest = temp_dir / "config.txt"
        dest.write_text("old")

        _update_text_file(dest, "new content")

        assert dest.read_text() == "new content"
        assert list(temp_dir.glob("config.*.txt")) == []

    def testUpdateTextFileNoBackupWhenSameContent(self, temp_dir):
        """Test that _update_text_file does not create backup-like files when unchanged."""
        dest = temp_dir / "config.txt"
        dest.write_text("same content")

        _update_text_file(dest, "same content")

        assert list(temp_dir.glob("config.*.txt")) == []


class TestDryRun:
    """Test that dry-run mode logs actions without writing any files."""

    def testCreateProjectDryRunNoFilesCreated(self, temp_dir, sample_project_name):
        """Test that createProject in dry-run mode does not create the project directory."""
        projectPath = temp_dir / sample_project_name

        createProject(str(projectPath), dryRun=True)

        assert (
            not projectPath.exists()
        ), "Project directory must not be created in dry-run mode"

    def testCreateProjectDryRunLogsActions(self, temp_dir, sample_project_name, caplog):
        """Test that createProject in dry-run mode logs the actions it would take."""
        projectPath = temp_dir / sample_project_name

        with caplog.at_level(logging.INFO):
            createProject(str(projectPath), dryRun=True)

        assert "creating project" in caplog.text
        assert "creating directories" in caplog.text
        assert "writing core files" in caplog.text

    def testUpdateProjectDryRunNoFilesModified(self, temp_dir, sample_project_name):
        """Test that updateProject in dry-run mode does not modify existing files."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        (projectPath / "src").mkdir()
        sentinel = projectPath / "src" / "globalVars.py"
        sentinel.write_text("original content")

        updateProject(str(projectPath), dryRun=True)

        assert (
            sentinel.read_text() == "original content"
        ), "File must not be modified in dry-run mode"

    def testUpdateProjectDryRunLogsActions(self, temp_dir, sample_project_name, caplog):
        """Test that updateProject in dry-run mode logs the actions it would take."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with caplog.at_level(logging.INFO):
            updateProject(str(projectPath), dryRun=True)

        assert "updating project" in caplog.text

    def testCopyIfNewerDryRunNoWrite(self, temp_dir):
        """Test that _copy_if_newer in dry-run mode does not write the destination file."""
        src = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"
        src.write_text("new content")

        _copy_if_newer(src, dest, dryRun=True)

        assert not dest.exists(), "Destination file must not be created in dry-run mode"

    def testUpdateTextFileDryRunNoWrite(self, temp_dir):
        """Test that _update_text_file in dry-run mode does not write the file."""
        dest = temp_dir / "output.txt"

        _update_text_file(dest, "some content", dryRun=True)

        assert not dest.exists(), "File must not be created in dry-run mode"


class TestCliFlags:
    """Test CLI flag handling for createProject."""

    def testMainPassesUiAndQtFlagsToCreateProject(self):
        with patch("organiseMyProjects.manageProject.createProject") as mockCreate:
            with patch(
                "sys.argv",
                ["manageProject.py", "demo", "--ui", "-qt", "--confirm"],
            ):
                createProjectMain()

        mockCreate.assert_called_once_with(
            "demo",
            dryRun=False,
            includeUi=True,
            includeQt=True,
        )

    def testMainPassesQtFlagToUpdateProject(self):
        with patch("organiseMyProjects.manageProject.updateProject") as mockUpdate:
            with patch(
                "sys.argv",
                ["manageProject.py", "--update", "-qt", "--confirm"],
            ):
                createProjectMain()

        mockUpdate.assert_called_once_with(
            Path.cwd(),
            dryRun=False,
            includeUi=False,
            includeQt=True,
        )

    def testMainPassesLegacyProjectFlagToCreateProject(self):
        with patch("organiseMyProjects.manageProject.createProject") as mockCreate:
            with patch(
                "sys.argv",
                ["manageProject.py", "--project", "demo", "--confirm"],
            ):
                createProjectMain()

        mockCreate.assert_called_once_with(
            "demo",
            dryRun=False,
            includeUi=False,
            includeQt=False,
        )

    def testMainPassesLegacyProjectFlagToUpdateProject(self):
        with patch("organiseMyProjects.manageProject.updateProject") as mockUpdate:
            with patch(
                "sys.argv",
                ["manageProject.py", "--update", "--project", "demo", "--confirm"],
            ):
                createProjectMain()

        mockUpdate.assert_called_once_with(
            "demo",
            dryRun=False,
            includeUi=False,
            includeQt=False,
        )

    def testMainPassesSyncFlagsToSyncModule(self):
        capturedArgv = []

        def fakeSyncMain():
            capturedArgv.extend(sys.argv)

        fakeSyncModule = types.SimpleNamespace(main=fakeSyncMain)

        with patch(
            "organiseMyProjects.manageProject._loadSyncModule",
            return_value=fakeSyncModule,
        ):
            with patch(
                "sys.argv",
                [
                    "manageProject.py",
                    "--sync",
                    "--confirm",
                    "--merge",
                    "--repo",
                    "Glawster/demo",
                    "--token",
                    "token123",
                    "--verbose",
                ],
            ):
                createProjectMain()

        assert capturedArgv == [
            "syncAgentInstructions.py",
            "--confirm",
            "--merge",
            "--repo",
            "Glawster/demo",
            "--token",
            "token123",
            "--verbose",
        ]
