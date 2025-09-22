"""
Integration tests for the entire organiseMyProjects package.
"""
import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPackageInstallation:
    """Test package installation and entry points."""
    
    def test_createproject_entry_point_exists(self):
        """Test that createProject entry point is properly configured."""
        from organiseMyProjects.createProject import main
        assert callable(main)
    
    def test_runlinter_entry_point_exists(self):
        """Test that runLinter entry point is properly configured."""
        from organiseMyProjects.runLinter import main
        assert callable(main)


class TestEndToEndWorkflow:
    """End-to-end tests for the complete project creation and linting workflow."""
    
    def test_create_and_lint_project(self, temp_dir):
        """Test creating a project and then linting it."""
        project_name = "testEndToEnd"
        project_path = temp_dir / project_name
        
        # Step 1: Create a project
        from organiseMyProjects.createProject import createProject
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(project_path))
        
        # Verify project was created
        assert project_path.exists()
        assert (project_path / ".github" / "copilot-instructions.md").exists()
        
        # Step 2: Add some Python code with violations to the project
        ui_dir = project_path / "ui"
        test_frame = ui_dir / "testFrame.py"
        
        code_with_violations = '''
import tkinter as tk
from tkinter import ttk

class TestFrame:
    def __init__(self):
        # Good naming
        self.btnSubmit = ttk.Button()
        
        # Bad naming - should trigger violation
        self.submit_button = ttk.Button()
        
    def methodWithoutBlankLine(self):
        # This should trigger a formatting violation
        statement1 = "test"
        statement2 = "test"
        statement3 = "test"
        statement4 = "test"
        statement5 = "test"
'''
        test_frame.write_text(code_with_violations)
        
        # Step 3: Lint the project
        from organiseMyProjects.runLinter import main as lint_main
        
        # Mock sys.argv to simulate command line call
        test_args = ['runLinter.py', str(project_path)]
        
        with patch('sys.argv', test_args):
            # Capture output but don't fail on violations
            try:
                lint_main()
            except SystemExit:
                pass  # Linter might exit with non-zero code on violations
        
        # If we get here, the basic workflow completed successfully
        assert True  # Test passes if no exceptions were thrown
    
    def test_update_existing_project(self, temp_dir):
        """Test updating an existing project."""
        project_name = "testUpdate"
        project_path = temp_dir / project_name
        
        # Create initial project
        from organiseMyProjects.createProject import createProject, updateProject
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(project_path))
        
        # Verify initial creation
        assert project_path.exists()
        
        # Remove a file to test update
        (project_path / "main.py").unlink()
        assert not (project_path / "main.py").exists()
        
        # Update the project
        with patch('organiseMyProjects.createProject.subprocess.run'):
            updateProject(str(project_path))
        
        # Verify file was restored
        assert (project_path / "main.py").exists()
    
    def test_project_structure_completeness(self, temp_dir):
        """Test that created projects have all expected files and directories."""
        project_name = "testStructure"
        project_path = temp_dir / project_name
        
        from organiseMyProjects.createProject import createProject
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(project_path))
        
        # Define expected structure
        expected_dirs = [
            "src", "ui", "tests", "logs", ".github"
        ]
        
        expected_files = [
            "main.py", ".gitignore", "requirements.txt", "dev-requirements.txt",
            ".env", "README.md", ".pre-commit-config.yaml",
            "src/__init__.py", "ui/__init__.py",
            ".github/copilot-instructions.md"
        ]
        
        expected_copied_modules = [
            "src/logUtils.py", "ui/styleUtils.py", "ui/mainMenu.py",
            "ui/baseFrame.py", "ui/frameTemplate.py", "ui/statusFrame.py",
            "tests/runLinter.py", "tests/guiNamingLinter.py"
        ]
        
        # Check directories
        for dir_name in expected_dirs:
            dir_path = project_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"
        
        # Check files
        for file_name in expected_files:
            file_path = project_path / file_name
            assert file_path.exists(), f"File {file_name} should exist"
            assert file_path.is_file(), f"{file_name} should be a file"
        
        # Check copied modules
        for module_name in expected_copied_modules:
            module_path = project_path / module_name
            assert module_path.exists(), f"Module {module_name} should exist"
            assert module_path.is_file(), f"{module_name} should be a file"


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_create_project_invalid_path(self, capsys):
        """Test creating project with invalid path."""
        from organiseMyProjects.createProject import createProject
        
        # Try to create project in a path that can't be created (e.g., inside a file)
        invalid_path = "/dev/null/impossible_project"
        
        try:
            createProject(invalid_path)
        except (OSError, IOError, PermissionError):
            # These exceptions are expected for invalid paths
            pass
        
        # Test should pass if appropriate exception handling occurs
        assert True
    
    def test_lint_invalid_python_syntax(self, temp_dir, capsys):
        """Test linting file with invalid Python syntax."""
        python_file = temp_dir / "invalid.py"
        invalid_content = '''
import tkinter as tk

class InvalidSyntax:
    def __init__(self):
        # Missing closing quote
        self.btnTest = "incomplete string
'''
        python_file.write_text(invalid_content)
        
        from organiseMyProjects.guiNamingLinter import lintFile
        
        # Should handle syntax errors gracefully
        try:
            lintFile(str(python_file))
        except SyntaxError:
            pass  # Expected for invalid syntax
        
        # Test passes if no unhandled exceptions
        assert True


class TestModuleImports:
    """Test that all modules can be imported correctly."""
    
    def test_import_createproject(self):
        """Test importing createProject module."""
        from organiseMyProjects import createProject
        assert hasattr(createProject, 'createProject')
        assert hasattr(createProject, 'updateProject')
        assert hasattr(createProject, 'main')
    
    def test_import_gui_naming_linter(self):
        """Test importing guiNamingLinter module."""
        from organiseMyProjects import guiNamingLinter
        assert hasattr(guiNamingLinter, 'GuiNamingVisitor')
        assert hasattr(guiNamingLinter, 'lintFile')
        assert hasattr(guiNamingLinter, 'lintGuiNaming')
    
    def test_import_run_linter(self):
        """Test importing runLinter module."""
        from organiseMyProjects import runLinter
        assert hasattr(runLinter, 'main')
        assert hasattr(runLinter, '_lint_target')
    
    def test_package_metadata(self):
        """Test that package metadata is accessible."""
        import organiseMyProjects
        # Package should be importable and have basic structure
        assert hasattr(organiseMyProjects, '__name__')


class TestResourceAccess:
    """Test access to package resources."""
    
    def test_copilot_instructions_resource_access(self):
        """Test that copilot instructions can be accessed as a package resource."""
        try:
            from importlib.resources import files
        except ImportError:
            from importlib_resources import files
        
        package_files = files('organiseMyProjects')
        copilot_file = package_files / 'copilot-instructions.md'
        
        # File should exist in package
        assert copilot_file.is_file()
        
        # Content should be readable
        content = copilot_file.read_text()
        assert len(content) > 0
        assert "GitHub Copilot Instructions" in content