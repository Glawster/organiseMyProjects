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
    
    def test_create_project_basic_structure(self, temp_dir, sample_project_name):
        """Test that createProject creates the basic directory structure."""
        project_path = temp_dir / sample_project_name
        
        # Mock subprocess to avoid git/pre-commit dependencies
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(project_path))
        
        # Verify directory structure
        assert project_path.exists()
        assert (project_path / "src").exists()
        assert (project_path / "ui").exists() 
        assert (project_path / "tests").exists()
        assert (project_path / "logs").exists()
        assert (project_path / ".github").exists()
        
        # Verify package init files
        assert (project_path / "src" / "__init__.py").exists()
        assert (project_path / "ui" / "__init__.py").exists()
    
    def test_create_project_core_files(self, temp_dir, sample_project_name):
        """Test that createProject creates core configuration files."""
        project_path = temp_dir / sample_project_name
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(project_path))
        
        # Verify core files exist
        assert (project_path / ".gitignore").exists()
        assert (project_path / "requirements.txt").exists()
        assert (project_path / "dev-requirements.txt").exists()
        assert (project_path / ".env").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / "main.py").exists()
        assert (project_path / ".pre-commit-config.yaml").exists()
    
    def test_create_project_file_contents(self, temp_dir, sample_project_name):
        """Test that createProject creates files with correct content."""
        project_path = temp_dir / sample_project_name
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(project_path))
        
        # Verify file contents
        assert (project_path / ".gitignore").read_text() == GITIGNORE_CONTENT
        assert (project_path / "requirements.txt").read_text() == REQUIREMENTS_CONTENT
        assert (project_path / "dev-requirements.txt").read_text() == DEV_REQUIREMENTS_CONTENT
        assert (project_path / ".env").read_text() == ENV_CONTENT
        assert (project_path / "main.py").read_text() == MAIN_PY_CONTENT
        assert (project_path / ".pre-commit-config.yaml").read_text() == PRECOMMIT_CONTENT
        
        # Verify README content
        readme_content = (project_path / "README.md").read_text()
        assert sample_project_name in readme_content
        assert "Project scaffold created by createProject.py" in readme_content
    
    def test_create_project_already_exists(self, temp_dir, sample_project_name, capsys):
        """Test behavior when project directory already exists."""
        project_path = temp_dir / sample_project_name
        project_path.mkdir()  # Create directory first
        
        createProject(str(project_path))
        
        captured = capsys.readouterr()
        assert "already exists" in captured.out
    
    def test_create_project_copilot_instructions(self, temp_dir, sample_project_name):
        """Test that copilot instructions are copied from package resources."""
        project_path = temp_dir / sample_project_name
        
        # Mock the package resource access
        with patch('organiseMyProjects.createProject.files') as mock_files:
            mock_package_files = mock_files.return_value
            mock_copilot_file = mock_package_files.__truediv__.return_value
            mock_copilot_file.is_file.return_value = True
            mock_copilot_file.read_text.return_value = "# GitHub Copilot Instructions\nTest content"
            
            with patch('organiseMyProjects.createProject.subprocess.run'):
                createProject(str(project_path))
        
        # Verify copilot instructions file was created
        copilot_file = project_path / ".github" / "copilot-instructions.md"
        assert copilot_file.exists()
        assert "# GitHub Copilot Instructions" in copilot_file.read_text()


class TestUpdateProject:
    """Test cases for updateProject function."""
    
    def test_update_project_existing(self, temp_dir, sample_project_name):
        """Test updating an existing project."""
        project_path = temp_dir / sample_project_name
        project_path.mkdir()
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            updateProject(str(project_path))
        
        # Verify directories are created
        assert (project_path / "src").exists()
        assert (project_path / "ui").exists()
        assert (project_path / "tests").exists()
        assert (project_path / "logs").exists()
        assert (project_path / ".github").exists()
    
    def test_update_project_nonexistent(self, temp_dir, sample_project_name, capsys):
        """Test behavior when trying to update non-existent project."""
        project_path = temp_dir / sample_project_name
        
        updateProject(str(project_path))
        
        captured = capsys.readouterr()
        assert "does not exist" in captured.out


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_copy_if_newer_new_file(self, temp_dir):
        """Test copying when destination doesn't exist."""
        src = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"
        
        src.write_text("test content")
        
        _copy_if_newer(src, dest)
        
        assert dest.exists()
        assert dest.read_text() == "test content"
    
    def test_copy_if_newer_older_dest(self, temp_dir):
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
    
    def test_update_text_file_new(self, temp_dir):
        """Test updating text file when it doesn't exist."""
        dest = temp_dir / "test.txt"
        content = "test content"
        
        _update_text_file(dest, content)
        
        assert dest.exists()
        assert dest.read_text() == content
    
    def test_update_text_file_same_content(self, temp_dir):
        """Test updating text file when content is the same."""
        dest = temp_dir / "test.txt"
        content = "test content"
        
        dest.write_text(content)
        original_mtime = dest.stat().st_mtime
        
        _update_text_file(dest, content)
        
        # File should not be modified if content is the same
        assert dest.stat().st_mtime == original_mtime
    
    def test_update_text_file_different_content(self, temp_dir):
        """Test updating text file when content is different."""
        dest = temp_dir / "test.txt"
        old_content = "old content"
        new_content = "new content"
        
        dest.write_text(old_content)
        
        _update_text_file(dest, new_content)
        
        assert dest.read_text() == new_content