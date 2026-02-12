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
    widgetClasses,
    detectFramework,
    isSnakeCase,
    qtWidgetTypes
)


class TestGuiNamingVisitor:
    """Test cases for GuiNamingVisitor class."""
    
    def testVisitorInitialization(self):
        """Test that visitor initializes correctly."""
        lines = ["line1", "line2", "line3"]
        visitor = GuiNamingVisitor(lines)
        
        assert visitor.lines == lines
        assert visitor.violations == []
        assert visitor.packCalls == 0
        assert visitor.gridCalls == 0
    
    def testNamingRulesStructure(self):
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
    
    def testWidgetClassesDefinition(self):
        """Test that widget classes are correctly defined."""
        expected_widgets = {
            'Button', 'Entry', 'Label', 'Frame', 'Text',
            'Listbox', 'Checkbutton', 'Radiobutton', 'Combobox'
        }
        
        assert widgetClasses == expected_widgets
        assert 'Handler' not in widgetClasses
        assert 'Constant' not in widgetClasses
        assert 'Class' not in widgetClasses
    
    def testClassNameExceptions(self):
        """Test that class name exceptions are defined."""
        assert 'iCloudSyncFrame' in classNameExceptions


class TestLintFile:
    """Test cases for lintFile function."""
    
    def testLintFileWithViolations(self, mockPythonFile, capsys):
        """Test linting a file that contains violations."""
        lintFile(str(mockPythonFile))
        
        captured = capsys.readouterr()
        
        # Should report violations
        assert "invalid_button" in captured.out
        assert "Button" in captured.out
        assert str(mockPythonFile) in captured.out
    
    def testLintNonexistentFile(self, temp_dir, capsys):
        """Test linting a file that doesn't exist."""
        nonexistent_file = temp_dir / "nonexistent.py"
        
        lintFile(str(nonexistent_file))
        
        captured = capsys.readouterr()
        assert "does not exist" in captured.out or "No such file" in captured.out
    
    def testLintValidPythonFile(self, temp_dir, capsys):
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
    
    def testLintDirectory(self, temp_dir, capsys):
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
    
    def testLintEmptyDirectory(self, temp_dir, capsys):
        """Test linting an empty directory."""
        lintGuiNaming(str(temp_dir))
        
        captured = capsys.readouterr()
        # Should handle empty directory gracefully
        assert "Checking GUI naming" in captured.out
    
    def testLintDirectoryWithSubdirs(self, temp_dir, capsys):
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
    def testValidNamingPatterns(self, valid_name, widget_type):
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
    def testInvalidNamingPatterns(self, invalid_name, widget_type):
        """Test that invalid names don't match their respective patterns."""
        import re
        pattern = namingRules[widget_type]
        assert not re.match(pattern, invalid_name), f"{invalid_name} should not match {widget_type} pattern"


class TestSpecialCases:
    """Test cases for special scenarios."""
    
    def testIcloudException(self):
        """Test that iCloud-related class names are handled as exceptions."""
        assert 'iCloudSyncFrame' in classNameExceptions
    
    def testWidgetClassesSubset(self):
        """Test that widgetClasses excludes non-widget types."""
        assert 'Handler' not in widgetClasses
        assert 'Constant' not in widgetClasses  
        assert 'Class' not in widgetClasses
        assert 'Button' in widgetClasses
        assert 'Label' in widgetClasses


class TestFrameworkDetection:
    """Test cases for framework detection."""
    
    def testDetectTkinter(self):
        """Test detection of Tkinter framework."""
        content = "import tkinter as tk\nfrom tkinter import ttk"
        assert detectFramework(content) == 'tkinter'
        
        content2 = "from tkinter import *"
        assert detectFramework(content2) == 'tkinter'
    
    def testDetectQt(self):
        """Test detection of Qt frameworks."""
        content1 = "from PySide6.QtWidgets import QWidget"
        assert detectFramework(content1) == 'qt'
        
        content2 = "from PyQt5.QtCore import Qt"
        assert detectFramework(content2) == 'qt'
        
        content3 = "from PyQt6.QtWidgets import QApplication"
        assert detectFramework(content3) == 'qt'
    
    def testDetectNoFramework(self):
        """Test files without recognized GUI framework."""
        content = "import os\nimport sys"
        assert detectFramework(content) is None


class TestSnakeCase:
    """Test cases for snake_case validation."""
    
    @pytest.mark.parametrize("valid_name", [
        "save_button",
        "title_label",
        "username_input",
        "_internal_widget",
        "_private_member",
        "button2",
        "test_widget_2",
        "x",  # Single character
        "i",  # Single character
        "_x",  # Private single character
    ])
    def testValidSnakeCase(self, valid_name):
        """Test that valid snake_case names pass validation."""
        assert isSnakeCase(valid_name), f"{valid_name} should be valid snake_case"
    
    @pytest.mark.parametrize("invalid_name", [
        "saveButton",  # camelCase
        "SaveButton",  # PascalCase
        "btnSave",     # prefix style
        "CONSTANT",    # all caps
        "save-button", # hyphens
        "2button",     # starts with number
        "",            # empty string
    ])
    def testInvalidSnakeCase(self, invalid_name):
        """Test that invalid snake_case names fail validation."""
        assert not isSnakeCase(invalid_name), f"{invalid_name} should not be valid snake_case"


class TestQtWidgets:
    """Test cases for Qt widget types."""
    
    def testQtWidgetTypes(self):
        """Test that common Qt widgets are defined."""
        assert 'QPushButton' in qtWidgetTypes
        assert 'QLabel' in qtWidgetTypes
        assert 'QLineEdit' in qtWidgetTypes
        assert 'QWidget' in qtWidgetTypes
        assert 'QComboBox' in qtWidgetTypes


class TestQtNamingValidation:
    """Test cases for Qt widget naming validation."""
    
    def testQtValidNaming(self, mockQtFile, capsys):
        """Test that valid Qt naming passes."""
        from organiseMyProjects.guiNamingLinter import checkFile
        violations = checkFile(str(mockQtFile))
        
        # Should have one violation for invalidButton (not snake_case)
        assert len(violations) == 1
        assert 'invalidButton' in str(violations[0])
    
    def testQtSnakeCaseViolation(self, temp_dir):
        """Test that camelCase in Qt files is flagged."""
        qt_file = temp_dir / "test_qt.py"
        content = '''
from PySide6.QtWidgets import QPushButton

class MyWidget:
    def __init__(self):
        self.saveButton = QPushButton()  # Invalid - not snake_case
'''
        qt_file.write_text(content)
        
        from organiseMyProjects.guiNamingLinter import checkFile
        violations = checkFile(str(qt_file))
        
        assert len(violations) > 0
        assert any('saveButton' in str(v) for v in violations)
    
    def testQtPrivateMembersValid(self, temp_dir):
        """Test that Qt private members with leading underscore are valid."""
        qt_file = temp_dir / "test_qt_private.py"
        content = '''
from PySide6.QtWidgets import QWidget

class MyWidget:
    def __init__(self):
        self._internal_widget = QWidget()  # Valid - private snake_case
'''
        qt_file.write_text(content)
        
        from organiseMyProjects.guiNamingLinter import checkFile
        violations = checkFile(str(qt_file))
        
        # Should have no violations for private members in snake_case
        assert len(violations) == 0
    
    def testQtMultipleWidgets(self, temp_dir):
        """Test validation with multiple Qt widgets."""
        qt_file = temp_dir / "test_qt_multi.py"
        content = '''
from PySide6.QtWidgets import QPushButton, QLabel, QLineEdit

class MyWidget:
    def __init__(self):
        self.save_button = QPushButton()  # Valid
        self.title_label = QLabel()  # Valid
        self.usernameInput = QLineEdit()  # Invalid - camelCase
        self.btnCancel = QPushButton()  # Invalid - not snake_case
'''
        qt_file.write_text(content)
        
        from organiseMyProjects.guiNamingLinter import checkFile
        violations = checkFile(str(qt_file))
        
        # Should have 2 violations
        assert len(violations) == 2
        assert any('usernameInput' in str(v) for v in violations)
        assert any('btnCancel' in str(v) for v in violations)


class TestMixedProjects:
    """Test cases for projects with both Tkinter and Qt files."""
    
    def testMixedProjectLinting(self, temp_dir, capsys):
        """Test linting a directory with both Tkinter and Qt files."""
        # Create Tkinter file
        tk_file = temp_dir / "tkinter_app.py"
        tk_content = '''
import tkinter as tk

class TkFrame:
    def __init__(self):
        self.btnSave = tk.Button()  # Valid Tkinter
'''
        tk_file.write_text(tk_content)
        
        # Create Qt file
        qt_file = temp_dir / "qt_app.py"
        qt_content = '''
from PySide6.QtWidgets import QPushButton

class QtWidget:
    def __init__(self):
        self.save_button = QPushButton()  # Valid Qt
'''
        qt_file.write_text(qt_content)
        
        lintGuiNaming(str(temp_dir))
        
        captured = capsys.readouterr()
        
        # Both files should be processed and marked as OK
        assert "tkinter_app.py" in captured.out
        assert "qt_app.py" in captured.out
    
    def testTkinterRulesNotAppliedToQt(self, temp_dir):
        """Test that Tkinter prefix rules are not applied to Qt files."""
        qt_file = temp_dir / "test_qt.py"
        content = '''
from PySide6.QtWidgets import QPushButton

class MyWidget:
    def __init__(self):
        self.save_button = QPushButton()  # Valid Qt, no btn prefix needed
'''
        qt_file.write_text(content)
        
        from organiseMyProjects.guiNamingLinter import checkFile
        violations = checkFile(str(qt_file))
        
        # Should have no violations - Qt doesn't require btn prefix
        assert len(violations) == 0
    
    def testQtRulesNotAppliedToTkinter(self, temp_dir):
        """Test that Qt snake_case rules are not applied to Tkinter files."""
        tk_file = temp_dir / "test_tk.py"
        content = '''
import tkinter as tk

class MyFrame:
    def __init__(self):
        self.btnSave = tk.Button()  # Valid Tkinter, not snake_case
'''
        tk_file.write_text(content)
        
        from organiseMyProjects.guiNamingLinter import checkFile
        violations = checkFile(str(tk_file))
        
        # Should have no violations - Tkinter allows prefix-based camelCase
        assert len(violations) == 0