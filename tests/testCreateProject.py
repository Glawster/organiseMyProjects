"""
Tests for createProject.py functionality.
"""
import datetime
import logging
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.createProject import (
    createProject, 
    updateProject, 
    _backup_file,
    _copy_if_newer, 
    _update_text_file,
    GITIGNORE_CONTENT,
    REQUIREMENTS_CONTENT,
    DEV_REQUIREMENTS_CONTENT,
    ENV_CONTENT,
    MAIN_PY_CONTENT,
    PRECOMMIT_CONTENT,
    PYTEST_INI_CONTENT,
    VSCODE_SETTINGS_CONTENT,
)


class TestCreateProject:
    """Test cases for createProject function."""
    
    def testCreateProjectBasicStructure(self, temp_dir, sample_project_name):
        """Test that createProject creates the basic directory structure."""
        projectPath = temp_dir / sample_project_name
        
        # Mock subprocess to avoid git/pre-commit dependencies
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))
        
        # Verify directory structure
        assert projectPath.exists()
        assert (projectPath / "src").exists()
        assert (projectPath / "ui").exists() 
        assert (projectPath / "tests").exists()
        assert (projectPath / "logs").exists()
        assert (projectPath / ".github").exists()
        
        # Verify package init files
        assert (projectPath / "src" / "__init__.py").exists()
        assert (projectPath / "ui" / "__init__.py").exists()
    
    def testCreateProjectCoreFiles(self, temp_dir, sample_project_name):
        """Test that createProject creates core configuration files."""
        projectPath = temp_dir / sample_project_name
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))
        
        # Verify core files exist
        assert (projectPath / ".gitignore").exists()
        assert (projectPath / "requirements.txt").exists()
        assert (projectPath / "dev-requirements.txt").exists()
        assert (projectPath / ".env").exists()
        assert (projectPath / "README.md").exists()
        assert (projectPath / "main.py").exists()
        assert (projectPath / ".pre-commit-config.yaml").exists()
    
    def testCreateProjectFileContents(self, temp_dir, sample_project_name):
        """Test that createProject creates files with correct content."""
        projectPath = temp_dir / sample_project_name
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))
        
        # Verify file contents
        assert (projectPath / ".gitignore").read_text() == GITIGNORE_CONTENT
        assert (projectPath / "requirements.txt").read_text() == REQUIREMENTS_CONTENT
        assert (projectPath / "dev-requirements.txt").read_text() == DEV_REQUIREMENTS_CONTENT
        assert (projectPath / ".env").read_text() == ENV_CONTENT
        assert (projectPath / "main.py").read_text() == MAIN_PY_CONTENT
        assert (projectPath / ".pre-commit-config.yaml").read_text() == PRECOMMIT_CONTENT
        
        # Verify README content
        readmeContent = (projectPath / "README.md").read_text()
        assert sample_project_name in readmeContent
        assert "Project scaffold created by createProject.py" in readmeContent

    def testCreateProjectPytestIni(self, temp_dir, sample_project_name):
        """Test that createProject creates pytest.ini with the correct content."""
        projectPath = temp_dir / sample_project_name

        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))

        assert (projectPath / "pytest.ini").exists()
        assert (projectPath / "pytest.ini").read_text() == PYTEST_INI_CONTENT

    def testCreateProjectVscodeSettings(self, temp_dir, sample_project_name):
        """Test that createProject creates .vscode/settings.json with the correct content."""
        projectPath = temp_dir / sample_project_name

        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))

        assert (projectPath / ".vscode" / "settings.json").exists()
        assert (projectPath / ".vscode" / "settings.json").read_text() == VSCODE_SETTINGS_CONTENT
    
    def testCreateProjectTemplateFiles(self, temp_dir, sample_project_name):
        """Test that only template files (not package utilities) are copied."""
        projectPath = temp_dir / sample_project_name
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))
        
        # Verify template files are copied
        assert (projectPath / "src" / "globalVars.py").exists(), "globalVars.py should be copied to new projects"
        assert (projectPath / "ui" / "styleUtils.py").exists()
        assert (projectPath / "ui" / "mainMenu.py").exists()
        assert (projectPath / "ui" / "baseFrame.py").exists()
        assert (projectPath / "ui" / "frameTemplate.py").exists()
        assert (projectPath / "ui" / "statusFrame.py").exists()
        assert (projectPath / "tests" / "runLinter.py").exists()
        assert (projectPath / "tests" / "guiNamingLinter.py").exists()
        
        # Verify package utilities are NOT copied
        assert not (projectPath / "src" / "logUtils.py").exists(), "logUtils.py should NOT be copied to new projects"
        assert not (projectPath / "createProject.py").exists(), "createProject.py should NOT be copied to new projects"
    
    def testCreateProjectAlreadyExists(self, temp_dir, sample_project_name, caplog):
        """Test behavior when project directory already exists."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()  # Create directory first
        
        with caplog.at_level(logging.INFO):
            createProject(str(projectPath))
        
        assert "already exists" in caplog.text
    
    def testCreateProjectCopilotInstructions(self, temp_dir, sample_project_name):
        """Test that copilot instructions are copied from the .github/ directory."""
        projectPath = temp_dir / sample_project_name

        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))

        copilotFile = projectPath / ".github" / "copilot-instructions.md"
        assert copilotFile.exists()
        assert len(copilotFile.read_text()) > 0


class TestUpdateProject:
    """Test cases for updateProject function."""
    
    def testUpdateProjectExisting(self, temp_dir, sample_project_name):
        """Test updating an existing project."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            updateProject(str(projectPath))
        
        # Verify directories are created
        assert (projectPath / "src").exists()
        assert (projectPath / "ui").exists()
        assert (projectPath / "tests").exists()
        assert (projectPath / "logs").exists()
        assert (projectPath / ".github").exists()
    
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

        with patch('organiseMyProjects.createProject.subprocess.run'):
            updateProject(str(projectPath))

        assert (projectPath / "pytest.ini").exists()
        assert (projectPath / "pytest.ini").read_text() == PYTEST_INI_CONTENT

    def testUpdateProjectVscodeSettings(self, temp_dir, sample_project_name):
        """Test that updateProject creates/updates .vscode/settings.json with the correct content."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with patch('organiseMyProjects.createProject.subprocess.run'):
            updateProject(str(projectPath))

        assert (projectPath / ".vscode" / "settings.json").exists()
        assert (projectPath / ".vscode" / "settings.json").read_text() == VSCODE_SETTINGS_CONTENT

    def testUpdateProjectPytestIniOutdated(self, temp_dir, sample_project_name):
        """Test that updateProject updates pytest.ini if it is outdated."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        (projectPath / "pytest.ini").write_text("old content")

        with patch('organiseMyProjects.createProject.subprocess.run'):
            updateProject(str(projectPath))

        assert (projectPath / "pytest.ini").read_text() == PYTEST_INI_CONTENT

    def testUpdateProjectVscodeSettingsOutdated(self, temp_dir, sample_project_name):
        """Test that updateProject updates .vscode/settings.json if it is outdated."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        (projectPath / ".vscode").mkdir()
        (projectPath / ".vscode" / "settings.json").write_text('{"old": true}')

        with patch('organiseMyProjects.createProject.subprocess.run'):
            updateProject(str(projectPath))

        assert (projectPath / ".vscode" / "settings.json").read_text() == VSCODE_SETTINGS_CONTENT


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
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


class TestBackupFile:
    """Test cases for _backup_file helper."""

    def testBackupFileCreatesBackup(self, temp_dir):
        """Test that _backup_file renames existing file to stem.YYMMDD.ext."""
        dest = temp_dir / "globalVars.py"
        dest.write_text("original content")

        _backup_file(dest)

        stamp = datetime.date.today().strftime("%y%m%d")
        backup = temp_dir / f"globalVars.{stamp}.py"
        assert backup.exists(), "Backup file should be created"
        assert backup.read_text() == "original content"
        assert not dest.exists(), "Original file should be renamed away"

    def testBackupFileNoExistingFile(self, temp_dir):
        """Test that _backup_file does nothing when file doesn't exist."""
        dest = temp_dir / "nonexistent.py"
        _backup_file(dest)  # Should not raise
        assert not dest.exists()

    def testCopyIfNewerBacksUpBeforeOverwriting(self, temp_dir):
        """Test that _copy_if_newer creates a backup when overwriting."""
        import time

        src = temp_dir / "source.py"
        dest = temp_dir / "dest.py"

        dest.write_text("old content")
        time.sleep(0.05)
        src.write_text("new content")

        _copy_if_newer(src, dest)

        stamp = datetime.date.today().strftime("%y%m%d")
        backup = temp_dir / f"dest.{stamp}.py"
        assert backup.exists(), "Backup should exist after overwrite"
        assert backup.read_text() == "old content"
        assert dest.read_text() == "new content"

    def testUpdateTextFileBacksUpBeforeOverwriting(self, temp_dir):
        """Test that _update_text_file creates a backup when overwriting."""
        dest = temp_dir / "config.txt"
        dest.write_text("old")

        _update_text_file(dest, "new content")

        stamp = datetime.date.today().strftime("%y%m%d")
        backup = temp_dir / f"config.{stamp}.txt"
        assert backup.exists(), "Backup should exist after overwrite"
        assert backup.read_text() == "old"
        assert dest.read_text() == "new content"

    def testUpdateTextFileNoBackupWhenSameContent(self, temp_dir):
        """Test that _update_text_file does NOT create a backup when content is unchanged."""
        dest = temp_dir / "config.txt"
        dest.write_text("same content")

        _update_text_file(dest, "same content")

        stamp = datetime.date.today().strftime("%y%m%d")
        backup = temp_dir / f"config.{stamp}.txt"
        assert not backup.exists(), "No backup should be created when content is unchanged"


class TestDryRun:
    """Test that dry-run mode logs actions without writing any files."""

    def testCreateProjectDryRunNoFilesCreated(self, temp_dir, sample_project_name):
        """Test that createProject in dry-run mode does not create the project directory."""
        projectPath = temp_dir / sample_project_name

        createProject(str(projectPath), dryRun=True)

        assert not projectPath.exists(), "Project directory must not be created in dry-run mode"

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

        assert sentinel.read_text() == "original content", "File must not be modified in dry-run mode"

    def testUpdateProjectDryRunLogsActions(self, temp_dir, sample_project_name, caplog):
        """Test that updateProject in dry-run mode logs the actions it would take."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with caplog.at_level(logging.INFO):
            updateProject(str(projectPath), dryRun=True)

        assert "updating project" in caplog.text

    def testBackupFileDryRunNoRename(self, temp_dir):
        """Test that _backup_file in dry-run mode does not rename the original file."""
        dest = temp_dir / "config.txt"
        dest.write_text("original")

        _backup_file(dest, dryRun=True)

        assert dest.exists(), "Original file must not be renamed in dry-run mode"

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