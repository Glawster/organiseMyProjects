"""
Test configuration and fixtures for organiseMyProjects.
"""
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def testFilePath(tmp_path):
    file = tmp_path / "example.py"
    file.write_text(
        "def greet(name):\n"
        "    return f'hello {name}'\n"
    )
    return file  # return Path; str(file) if your code expects a string

@pytest.fixture
def tempDir():
    """Create a temporary directory for testing."""
    tempPath = Path(tempfile.mkdtemp())
    yield tempPath
    shutil.rmtree(tempPath)


@pytest.fixture
def sampleProjectName():
    """Sample project name for testing."""
    return "testProject"


@pytest.fixture
def mockPythonFile(tempDir):
    """Create a sample Python file for testing the linter."""
    pythonFile = tempDir / "test_file.py"
    content = '''
import tkinter as tk
from tkinter import ttk

class TestFrame:
    def __init__(self):
        self.btnSave = ttk.Button()
        self.lblStatus = ttk.Label()
        self.invalid_button = ttk.Button()  # Should trigger naming violation
        
    def shortMethod(self):
        pass
        
    def longMethod(self):
        # Should trigger formatting violation - missing blank line after def
        line1 = "test"
        line2 = "test"
        line3 = "test"
        line4 = "test"
        line5 = "test"
'''
    pythonFile.write_text(content)
    return pythonFile