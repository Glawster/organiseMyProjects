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

from organiseMyProjects.runLinter import main, _lint_target


class TestRunLinter:
    """Test cases for runLinter functionality."""
    
    def test_lint_target_file(self, mock_python_file, capsys):
        """Test linting a single file."""
        with patch('organiseMyProjects.runLinter.lintFile') as mock_lint_file:
            _lint_target(str(mock_python_file))
            mock_lint_file.assert_called_once_with(str(mock_python_file))
        
        captured = capsys.readouterr()
        assert f"Linting: {mock_python_file}" in captured.out
    
    def test_lint_target_directory(self, temp_dir, capsys):
        """Test linting a directory."""
        with patch('organiseMyProjects.runLinter.lintGuiNaming') as mock_lint_gui:
            _lint_target(str(temp_dir))
            mock_lint_gui.assert_called_once_with(str(temp_dir))
        
        captured = capsys.readouterr()
        assert f"Linting: {temp_dir}" in captured.out
    
    def test_main_with_targets(self, mock_python_file):
        """Test main function with specific targets."""
        test_args = ['runLinter.py', str(mock_python_file)]
        
        with patch('sys.argv', test_args):
            with patch('organiseMyProjects.runLinter.lintFile') as mock_lint_file:
                main()
                mock_lint_file.assert_called_once_with(str(mock_python_file))
    
    def test_main_nonexistent_target(self, temp_dir, capsys):
        """Test main function with non-existent target."""
        nonexistent = temp_dir / "nonexistent.py"
        test_args = ['runLinter.py', str(nonexistent)]
        
        with patch('sys.argv', test_args):
            main()
        
        captured = capsys.readouterr()
        assert "does not exist" in captured.out
        assert "Skipping" in captured.out
    
    def test_main_non_python_target(self, temp_dir, capsys):
        """Test main function with non-Python file target."""
        text_file = temp_dir / "readme.txt"
        text_file.write_text("This is not Python")
        
        test_args = ['runLinter.py', str(text_file)]
        
        with patch('sys.argv', test_args):
            main()
        
        captured = capsys.readouterr()
        assert "not a Python file" in captured.out
        assert "Skipping" in captured.out
    
    def test_main_unreadable_target(self, temp_dir, capsys):
        """Test main function with unreadable target."""
        python_file = temp_dir / "test.py"
        python_file.write_text("# Python file")
        
        test_args = ['runLinter.py', str(python_file)]
        
        # Mock os.access to return False for read permission
        with patch('sys.argv', test_args):
            with patch('organiseMyProjects.runLinter.os.access', return_value=False):
                main()
        
        captured = capsys.readouterr()
        assert "not readable" in captured.out
        assert "Skipping" in captured.out
    
    def test_main_no_targets_with_project_dirs(self, temp_dir, capsys):
        """Test main function with no targets but project directories exist."""
        # Create project directories
        (temp_dir / "src").mkdir()
        (temp_dir / "ui").mkdir()
        (temp_dir / "tests").mkdir()
        
        test_args = ['runLinter.py']
        
        with patch('sys.argv', test_args):
            with patch('organiseMyProjects.runLinter.os.getcwd', return_value=str(temp_dir)):
                with patch('organiseMyProjects.runLinter.lintGuiNaming') as mock_lint_gui:
                    main()
                    
                    # Should lint each project directory
                    assert mock_lint_gui.call_count == 3
                    mock_lint_gui.assert_any_call("src")
                    mock_lint_gui.assert_any_call("ui") 
                    mock_lint_gui.assert_any_call("tests")
        
        captured = capsys.readouterr()
        assert "No target supplied" in captured.out
    
    def test_main_no_targets_no_project_dirs(self, temp_dir, capsys):
        """Test main function with no targets and no project directories."""
        test_args = ['runLinter.py']
        
        with patch('sys.argv', test_args):
            with patch('organiseMyProjects.runLinter.os.getcwd', return_value=str(temp_dir)):
                with patch('organiseMyProjects.runLinter.lintGuiNaming') as mock_lint_gui:
                    main()
                    
                    # Should lint current directory
                    mock_lint_gui.assert_called_once_with(".")
        
        captured = capsys.readouterr()
        assert "No target supplied" in captured.out


class TestIntegration:
    """Integration tests for the complete linting workflow."""
    
    def test_full_linting_workflow(self, temp_dir, capsys):
        """Test the complete linting workflow from command line to output."""
        # Create a Python file with various violations
        python_file = temp_dir / "gui_test.py"
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
        python_file.write_text(content)
        
        # Run the linter
        test_args = ['runLinter.py', str(python_file)]
        
        with patch('sys.argv', test_args):
            main()
        
        captured = capsys.readouterr()
        
        # Verify that violations were detected and reported
        assert str(python_file) in captured.out
        assert "save_button" in captured.out or "status_label" in captured.out
    
    def test_directory_linting_workflow(self, temp_dir, capsys):
        """Test linting an entire directory structure."""
        # Create subdirectories
        src_dir = temp_dir / "src"
        ui_dir = temp_dir / "ui"
        src_dir.mkdir()
        ui_dir.mkdir()
        
        # Create Python files in subdirectories
        (src_dir / "utils.py").write_text('''
def good_function():
    pass
''')
        
        (ui_dir / "main_frame.py").write_text('''
import tkinter as tk

class MainFrame:
    def __init__(self):
        self.btnClose = tk.Button()  # Good naming
        self.bad_button = tk.Button()  # Bad naming
''')
        
        # Run linter on directory
        test_args = ['runLinter.py', str(temp_dir)]
        
        with patch('sys.argv', test_args):
            main()
        
        captured = capsys.readouterr()
        
        # Verify output contains information about the directory scan
        assert f"Linting: {temp_dir}" in captured.out