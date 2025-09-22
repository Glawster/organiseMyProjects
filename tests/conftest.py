"""
Test configuration and fixtures for organiseMyProjects.
"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_project_name():
    """Sample project name for testing."""
    return "testProject"


@pytest.fixture
def mock_python_file(temp_dir):
    """Create a sample Python file for testing the linter."""
    python_file = temp_dir / "test_file.py"
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
    python_file.write_text(content)
    return python_file