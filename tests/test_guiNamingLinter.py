"""
Tests for guiNamingLinter.py functionality.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.guiNamingLinter import (
    GuiNamingVisitor,
    lintFile,
    lintGuiNaming,
    namingRules,
    classNameExceptions,
    widgetClasses
)


class TestGuiNamingVisitor:
    """Test cases for GuiNamingVisitor class."""
    
    def test_visitor_initialization(self):
        """Test that visitor initializes correctly."""
        lines = ["line1", "line2", "line3"]
        visitor = GuiNamingVisitor(lines)
        
        assert visitor.lines == lines
        assert visitor.violations == []
        assert visitor.packCalls == 0
        assert visitor.gridCalls == 0
    
    def test_naming_rules_structure(self):
        """Test that naming rules are properly defined."""
        expected_widget_types = {
            'Button', 'Entry', 'Label', 'Frame', 'Text', 
            'Listbox', 'Checkbutton', 'Radiobutton', 'Combobox'
        }
        
        assert 'Button' in namingRules
        assert 'Handler' in namingRules
        assert 'Constant' in namingRules
        assert 'Class' in namingRules
        
        # Test button naming pattern
        assert namingRules['Button'] == r'^btn[A-Z]\w+'
        assert namingRules['Handler'] == r'^on[A-Z]\w+'
        assert namingRules['Constant'] == r'^[A-Z_]+$'
        assert namingRules['Class'] == r'^[A-Z][a-zA-Z0-9]*$'
    
    def test_widget_classes_definition(self):
        """Test that widget classes are correctly defined."""
        expected_widgets = {
            'Button', 'Entry', 'Label', 'Frame', 'Text',
            'Listbox', 'Checkbutton', 'Radiobutton', 'Combobox'
        }
        
        assert widgetClasses == expected_widgets
        assert 'Handler' not in widgetClasses
        assert 'Constant' not in widgetClasses
        assert 'Class' not in widgetClasses
    
    def test_class_name_exceptions(self):
        """Test that class name exceptions are defined."""
        assert 'iCloudSyncFrame' in classNameExceptions


class TestLintFile:
    """Test cases for lintFile function."""
    
    def test_lint_file_with_violations(self, mock_python_file, capsys):
        """Test linting a file that contains violations."""
        lintFile(str(mock_python_file))
        
        captured = capsys.readouterr()
        
        # Should report violations
        assert "invalid_button" in captured.out
        assert "Button" in captured.out
        assert str(mock_python_file) in captured.out
    
    def test_lint_nonexistent_file(self, temp_dir, capsys):
        """Test linting a file that doesn't exist."""
        nonexistent_file = temp_dir / "nonexistent.py"
        
        lintFile(str(nonexistent_file))
        
        captured = capsys.readouterr()
        assert "does not exist" in captured.out or "No such file" in captured.out
    
    def test_lint_valid_python_file(self, temp_dir, capsys):
        """Test linting a valid Python file with no violations."""
        valid_file = temp_dir / "valid.py"
        content = '''
import tkinter as tk
from tkinter import ttk

class ValidFrame:
    def __init__(self):
        self.btnSave = ttk.Button()
        self.lblStatus = ttk.Label()
        
    def shortMethod(self):
        pass
        
    def longMethod(self):
        
        line1 = "test"
        line2 = "test"
        line3 = "test"
        line4 = "test"
        line5 = "test"
'''
        valid_file.write_text(content)
        
        lintFile(str(valid_file))
        
        captured = capsys.readouterr()
        assert "OK" in captured.out


class TestLintGuiNaming:
    """Test cases for lintGuiNaming function."""
    
    def test_lint_directory(self, temp_dir, capsys):
        """Test linting a directory containing Python files."""
        # Create a Python file with violations
        python_file = temp_dir / "test.py"
        content = '''
class TestClass:
    def __init__(self):
        self.invalid_button = None  # Should trigger violation
'''
        python_file.write_text(content)
        
        # Create a non-Python file (should be ignored)
        text_file = temp_dir / "readme.txt"
        text_file.write_text("This is not Python")
        
        lintGuiNaming(str(temp_dir))
        
        captured = capsys.readouterr()
        assert "test.py" in captured.out
        assert "readme.txt" not in captured.out
    
    def test_lint_empty_directory(self, temp_dir, capsys):
        """Test linting an empty directory."""
        lintGuiNaming(str(temp_dir))
        
        captured = capsys.readouterr()
        # Should handle empty directory gracefully
        assert "Checking GUI naming" in captured.out
    
    def test_lint_directory_with_subdirs(self, temp_dir, capsys):
        """Test linting a directory with subdirectories."""
        # Create subdirectory with Python file
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        python_file = subdir / "nested.py"
        content = '''
class NestedClass:
    def __init__(self):
        self.btnGood = None
'''
        python_file.write_text(content)
        
        lintGuiNaming(str(temp_dir))
        
        captured = capsys.readouterr()
        assert "nested.py" in captured.out


class TestNamingPatterns:
    """Test cases for specific naming patterns."""
    
    @pytest.mark.parametrize("valid_name,widget_type", [
        ("btnSave", "Button"),
        ("lblStatus", "Label"),
        ("entryName", "Entry"),
        ("frmMain", "Frame"),
        ("txtContent", "Text"),
        ("lstItems", "Listbox"),
        ("chkEnabled", "Checkbutton"),
        ("rdoOption", "Radiobutton"),
        ("cmbSelection", "Combobox"),
        ("onSaveClick", "Handler"),
        ("CONSTANT_VALUE", "Constant"),
        ("MyClass", "Class"),
    ])
    def test_valid_naming_patterns(self, valid_name, widget_type):
        """Test that valid names match their respective patterns."""
        import re
        pattern = namingRules[widget_type]
        assert re.match(pattern, valid_name), f"{valid_name} should match {widget_type} pattern"
    
    @pytest.mark.parametrize("invalid_name,widget_type", [
        ("saveButton", "Button"),  # Wrong prefix
        ("status_label", "Label"),  # Snake case
        ("entry_name", "Entry"),   # Snake case
        ("main_frame", "Frame"),   # Snake case
        ("content_text", "Text"),  # Snake case
        ("item_list", "Listbox"),  # Wrong format
        ("enabled_check", "Checkbutton"), # Wrong format
        ("option_radio", "Radiobutton"),  # Wrong format
        ("selection_combo", "Combobox"),  # Wrong format
        ("saveClick", "Handler"),  # Missing 'on' prefix
        ("constantValue", "Constant"), # Not all caps
        ("myClass", "Class"),      # Should start with capital
    ])
    def test_invalid_naming_patterns(self, invalid_name, widget_type):
        """Test that invalid names don't match their respective patterns."""
        import re
        pattern = namingRules[widget_type]
        assert not re.match(pattern, invalid_name), f"{invalid_name} should not match {widget_type} pattern"


class TestSpecialCases:
    """Test cases for special scenarios."""
    
    def test_icloud_exception(self):
        """Test that iCloud-related class names are handled as exceptions."""
        assert 'iCloudSyncFrame' in classNameExceptions
    
    def test_widget_classes_subset(self):
        """Test that widgetClasses excludes non-widget types."""
        assert 'Handler' not in widgetClasses
        assert 'Constant' not in widgetClasses  
        assert 'Class' not in widgetClasses
        assert 'Button' in widgetClasses
        assert 'Label' in widgetClasses