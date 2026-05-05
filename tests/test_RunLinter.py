"""
Tests for runLinter.py functionality.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import argparse

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.runLinter import main, _lintTarget


class TestRunLinter:
    """Test cases for runLinter functionality."""
    
    def testLintTargetFile(self, mockPythonFile, capsys):
        """Test linting a single file."""
        with patch('organiseMyProjects.runLinter.lintFile') as mockLintFile:
            _lintTarget(str(mockPythonFile))
            mockLintFile.assert_called_once_with(str(mockPythonFile))
        
        captured = capsys.readouterr()
        assert f"Linting: {mockPythonFile}" in captured.out
    
    def testLintTargetDirectory(self, tempDir, capsys):
        """Test linting a directory."""
        with patch('organiseMyProjects.runLinter.lintGuiNaming') as mockLintGui:
            _lintTarget(str(tempDir))
            mockLintGui.assert_called_once_with(str(tempDir))
        
        captured = capsys.readouterr()
        assert f"Linting: {tempDir}" in captured.out
    
    def testMainWithTargets(self, testFilePath):
        """Test main function with specific targets."""
        testArgs = ['runLinter.py', str(testFilePath)]
        
        with patch('sys.argv', testArgs):
            with patch('organiseMyProjects.runLinter.lintFile') as mockLintFile:
                main()
                mockLintFile.assert_called_once_with(str(testFilePath))
    
    def testMainNonexistentTarget(self, tempDir, capsys):
        """Test main function with non-existent target."""
        nonexistent = tempDir / "nonexistent.py"
        testArgs = ['runLinter.py', str(nonexistent)]
        
        with patch('sys.argv', testArgs):
            main()
        
        captured = capsys.readouterr()
        assert "does not exist" in captured.out
        assert "Skipping" in captured.out
    
    def testMainNonPythonTarget(self, tempDir, capsys):
        """Test main function with non-Python file target."""
        textFile = tempDir / "readme.txt"
        textFile.write_text("This is not Python")
        
        testArgs = ['runLinter.py', str(textFile)]
        
        with patch('sys.argv', testArgs):
            main()
        
        captured = capsys.readouterr()
        assert "not a Python file" in captured.out
        assert "Skipping" in captured.out
    
    def testMainUnreadableTarget(self, tempDir, capsys):
        """Test main function with unreadable target."""
        pythonFile = tempDir / "test.py"
        pythonFile.write_text("# Python file")
        
        testArgs = ['runLinter.py', str(pythonFile)]
        
        # Mock os.access to return False for read permission
        with patch('sys.argv', testArgs):
            with patch('organiseMyProjects.runLinter.os.access', return_value=False):
                main()
        
        captured = capsys.readouterr()
        assert "not readable" in captured.out
        assert "Skipping" in captured.out
    
    def testMainNoTargetsWithProjectDirs(self, tempDir, capsys):
        """Test main function with no targets but project directories exist."""
        # Create project directories
        (tempDir / "src").mkdir()
        (tempDir / "ui").mkdir()
        (tempDir / "tests").mkdir()
        
        testArgs = ['runLinter.py']
        
        # Change to temp directory and run test
        import os
        originalCwd = os.getcwd()
        try:
            os.chdir(tempDir)
            
            # Verify directories exist before test
            assert os.path.isdir("src"), "src directory should exist"
            assert os.path.isdir("ui"), "ui directory should exist" 
            assert os.path.isdir("tests"), "tests directory should exist"
            
            with patch('sys.argv', testArgs):
                with patch('organiseMyProjects.runLinter.lintGuiNaming') as mockLintGui:
                    main()
                    
                    # Debug output for troubleshooting
                    actualCalls = [call.args[0] for call in mockLintGui.call_args_list]
                    
                    # Should lint each project directory
                    assert mockLintGui.call_count == 3, f"Expected 3 calls but got {mockLintGui.call_count}. Calls: {actualCalls}"
                    mockLintGui.assert_any_call("src")
                    mockLintGui.assert_any_call("ui") 
                    mockLintGui.assert_any_call("tests")
        finally:
            os.chdir(originalCwd)
        
        captured = capsys.readouterr()
        assert "No target supplied" in captured.out
    
    def testMainNoTargetsNoProjectDirs(self, tempDir, capsys):
        """Test main function with no targets and no project directories."""
        testArgs = ['runLinter.py']
        
        # Change to temp directory and run test
        import os
        originalCwd = os.getcwd()
        try:
            os.chdir(tempDir)
            
            # Verify no project directories exist
            assert not os.path.isdir("src"), "src directory should not exist"
            assert not os.path.isdir("ui"), "ui directory should not exist"
            assert not os.path.isdir("tests"), "tests directory should not exist"
            
            with patch('sys.argv', testArgs):
                with patch('organiseMyProjects.runLinter.lintGuiNaming') as mockLintGui:
                    main()
                    
                    # Should lint current directory since no project dirs found
                    assert mockLintGui.call_count == 1, f"Expected 1 call but got {mockLintGui.call_count}"
                    mockLintGui.assert_called_once_with(".")
        finally:
            os.chdir(originalCwd)
        
        captured = capsys.readouterr()
        assert "No target supplied" in captured.out


class TestIntegration:
    """Integration tests for the complete linting workflow."""
    
    def testFullLintingWorkflow(self, tempDir, capsys):
        """Test the complete linting workflow from command line to output."""
        # Create a Python file with various violations
        pythonFile = tempDir / "gui_test.py"
        content = '''
import tkinter as tk
from tkinter import ttk

class TestGUI:
    def __init__(self):
        # Good naming
        self.btnSave = ttk.Button()
        self.lblStatus = ttk.Label()
        
        # Bad naming - should trigger violations
        self.save_button = ttk.Button()
        self.status_label = ttk.Label()
        
    def shortMethod(self):
        pass
        
    def longMethodWithoutBlankLine(self):
        # Should trigger formatting violation
        line1 = "statement 1"
        line2 = "statement 2"
        line3 = "statement 3"
        line4 = "statement 4"
        line5 = "statement 5"
'''
        pythonFile.write_text(content)
        
        # Run the linter
        testArgs = ['runLinter.py', str(pythonFile)]
        
        with patch('sys.argv', testArgs):
            main()
        
        captured = capsys.readouterr()
        
        # Verify that violations were detected and reported
        assert str(pythonFile) in captured.out
        assert "save_button" in captured.out or "status_label" in captured.out
    
    def testDirectoryLintingWorkflow(self, tempDir, capsys):
        """Test linting an entire directory structure."""
        # Create subdirectories
        srcDir = tempDir / "src"
        uiDir = tempDir / "ui"
        srcDir.mkdir()
        uiDir.mkdir()
        
        # Create Python files in subdirectories
        (srcDir / "utils.py").write_text('''
def good_function():
    pass
''')
        
        (uiDir / "main_frame.py").write_text('''
import tkinter as tk

class MainFrame:
    def __init__(self):
        self.btnClose = tk.Button()  # Good naming
        self.bad_button = tk.Button()  # Bad naming
''')
        
        # Run linter on directory
        testArgs = ['runLinter.py', str(tempDir)]
        
        with patch('sys.argv', testArgs):
            main()
        
        captured = capsys.readouterr()
        
        # Verify output contains information about the directory scan
        assert f"Linting: {tempDir}" in captured.out