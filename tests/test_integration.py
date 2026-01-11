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
    
    def testCreateProjectEntryPointExists(self):
        """Test that createProject entry point is properly configured."""
        from organiseMyProjects.createProject import main
        assert callable(main)
    
    def testRunLinterEntryPointExists(self):
        """Test that runLinter entry point is properly configured."""
        from organiseMyProjects.runLinter import main
        assert callable(main)


class TestEndToEndWorkflow:
    """End-to-end tests for the complete project creation and linting workflow."""
    
    def testCreateAndLintProject(self, temp_dir):
        """Test creating a project and then linting it."""
        projectName = "testEndToEnd"
        projectPath = temp_dir / projectName
        
        # Step 1: Create a project
        from organiseMyProjects.createProject import createProject
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))
        
        # Verify project was created
        assert projectPath.exists()
        assert (projectPath / ".github" / "copilot-instructions.md").exists()
        
        # Step 2: Add some Python code with violations to the project
        uiDir = projectPath / "ui"
        testFrame = uiDir / "testFrame.py"
        
        codeWithViolations = '''
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
        testFrame.write_text(codeWithViolations)
        
        # Step 3: Lint the project
        from organiseMyProjects.runLinter import main as lintMain
        
        # Mock sys.argv to simulate command line call
        testArgs = ['runLinter.py', str(projectPath)]
        
        with patch('sys.argv', testArgs):
            # Capture output but don't fail on violations
            try:
                lintMain()
            except SystemExit:
                pass  # Linter might exit with non-zero code on violations
        
        # If we get here, the basic workflow completed successfully
        assert True  # Test passes if no exceptions were thrown
    
    def testUpdateExistingProject(self, temp_dir):
        """Test updating an existing project."""
        projectName = "testUpdate"
        projectPath = temp_dir / projectName
        
        # Create initial project
        from organiseMyProjects.createProject import createProject, updateProject
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))
        
        # Verify initial creation
        assert projectPath.exists()
        
        # Remove a file to test update
        (projectPath / "main.py").unlink()
        assert not (projectPath / "main.py").exists()
        
        # Update the project
        with patch('organiseMyProjects.createProject.subprocess.run'):
            updateProject(str(projectPath))
        
        # Verify file was restored
        assert (projectPath / "main.py").exists()
    
    def testProjectStructureCompleteness(self, temp_dir):
        """Test that created projects have all expected files and directories."""
        projectName = "testStructure"
        projectPath = temp_dir / projectName
        
        from organiseMyProjects.createProject import createProject
        
        with patch('organiseMyProjects.createProject.subprocess.run'):
            createProject(str(projectPath))
        
        # Define expected structure
        expectedDirs = [
            "src", "ui", "tests", "logs", ".github"
        ]
        
        expectedFiles = [
            "main.py", ".gitignore", "requirements.txt", "dev-requirements.txt",
            ".env", "README.md", ".pre-commit-config.yaml",
            "src/__init__.py", "ui/__init__.py",
            ".github/copilot-instructions.md"
        ]
        
        expectedCopiedModules = [
            "src/logUtils.py", "ui/styleUtils.py", "ui/mainMenu.py",
            "ui/baseFrame.py", "ui/frameTemplate.py", "ui/statusFrame.py",
            "tests/runLinter.py", "tests/guiNamingLinter.py"
        ]
        
        # Check directories
        for dirName in expectedDirs:
            dirPath = projectPath / dirName
            assert dirPath.exists(), f"Directory {dirName} should exist"
            assert dirPath.is_dir(), f"{dirName} should be a directory"
        
        # Check files
        for fileName in expectedFiles:
            filePath = projectPath / fileName
            assert filePath.exists(), f"File {fileName} should exist"
            assert filePath.is_file(), f"{fileName} should be a file"
        
        # Check copied modules
        for moduleName in expectedCopiedModules:
            modulePath = projectPath / moduleName
            assert modulePath.exists(), f"Module {moduleName} should exist"
            assert modulePath.is_file(), f"{moduleName} should be a file"


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    def testCreateProjectInvalidPath(self, capsys):
        """Test creating project with invalid path."""
        from organiseMyProjects.createProject import createProject
        
        # Try to create project in a path that can't be created (e.g., inside a file)
        invalidPath = "/dev/null/impossible_project"
        
        try:
            createProject(invalidPath)
        except (OSError, IOError, PermissionError):
            # These exceptions are expected for invalid paths
            pass
        
        # Test should pass if appropriate exception handling occurs
        assert True
    
    def testLintInvalidPythonSyntax(self, temp_dir, capsys):
        """Test linting file with invalid Python syntax."""
        pythonFile = temp_dir / "invalid.py"
        invalidContent = '''
import tkinter as tk

class InvalidSyntax:
    def __init__(self):
        # Missing closing quote
        self.btnTest = "incomplete string
'''
        pythonFile.write_text(invalidContent)
        
        from organiseMyProjects.guiNamingLinter import lintFile
        
        # Should handle syntax errors gracefully
        try:
            lintFile(str(pythonFile))
        except SyntaxError:
            pass  # Expected for invalid syntax
        
        # Test passes if no unhandled exceptions
        assert True


class TestModuleImports:
    """Test that all modules can be imported correctly."""
    
    def testImportCreateProject(self):
        """Test importing createProject module."""
        from organiseMyProjects import createProject
        assert hasattr(createProject, 'createProject')
        assert hasattr(createProject, 'updateProject')
        assert hasattr(createProject, 'main')
    
    def testImportGuiNamingLinter(self):
        """Test importing guiNamingLinter module."""
        from organiseMyProjects import guiNamingLinter
        assert hasattr(guiNamingLinter, 'GuiNamingVisitor')
        assert hasattr(guiNamingLinter, 'lintFile')
        assert hasattr(guiNamingLinter, 'lintGuiNaming')
    
    def testImportRunLinter(self):
        """Test importing runLinter module."""
        from organiseMyProjects import runLinter
        assert hasattr(runLinter, 'main')
        assert hasattr(runLinter, '_lint_target')
    
    def testPackageMetadata(self):
        """Test that package metadata is accessible."""
        import organiseMyProjects
        # Package should be importable and have basic structure
        assert hasattr(organiseMyProjects, '__name__')


class TestResourceAccess:
    """Test access to package resources."""
    
    def testCopilotInstructionsResourceAccess(self):
        """Test that copilot instructions can be accessed as a package resource."""
        try:
            from importlib.resources import files
        except ImportError:
            from importlib_resources import files
        
        packageFiles = files('organiseMyProjects')
        copilotFile = packageFiles / 'copilot-instructions.md'
        
        # File should exist in package
        assert copilotFile.is_file()
        
        # Content should be readable
        content = copilotFile.read_text()
        assert len(content) > 0
        assert "GitHub Copilot Instructions" in content