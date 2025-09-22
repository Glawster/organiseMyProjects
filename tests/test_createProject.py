"""
Tests for createProject.py functionality.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.createProject import (
    createProject, 
    updateProject, 
    _copy_if_newer, 
    _update_text_file,
    GITIGNORE_CONTENT,
    REQUIREMENTS_CONTENT,
    DEV_REQUIREMENTS_CONTENT,
    ENV_CONTENT,
    MAIN_PY_CONTENT,
    PRECOMMIT_CONTENT
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
    
    def testCreateProjectAlreadyExists(self, temp_dir, sample_project_name, capsys):
        """Test behavior when project directory already exists."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()  # Create directory first
        
        createProject(str(projectPath))
        
        captured = capsys.readouterr()
        assert "already exists" in captured.out
    
    def testCreateProjectCopilotInstructions(self, temp_dir, sample_project_name):
        """Test that copilot instructions are copied from package resources."""
        projectPath = temp_dir / sample_project_name
        
        # Mock the package resource access
        with patch('organiseMyProjects.createProject.files') as mock_files:
            mockPackageFiles = mock_files.return_value
            mockCopilotFile = mockPackageFiles.__truediv__.return_value
            mockCopilotFile.is_file.return_value = True
            mockCopilotFile.read_text.return_value = "# GitHub Copilot Instructions\nTest content"
            
            with patch('organiseMyProjects.createProject.subprocess.run'):
                createProject(str(projectPath))
        
        # Verify copilot instructions file was created
        copilotFile = projectPath / ".github" / "copilot-instructions.md"
        assert copilotFile.exists()
        assert "# GitHub Copilot Instructions" in copilotFile.read_text()


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
    
    def testUpdateProjectNonexistent(self, temp_dir, sample_project_name, capsys):
        """Test behavior when trying to update non-existent project."""
        projectPath = temp_dir / sample_project_name
        
        updateProject(str(projectPath))
        
        captured = capsys.readouterr()
        assert "does not exist" in captured.out


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