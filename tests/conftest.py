"""
Test configuration and fixtures for organiseMyProjects.
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

import organiseMyProjects.manageProject as manageProjectModule
from organiseMyProjects.logUtils import getLogger, setApplication


@pytest.fixture(autouse=True)
def configureOmpLogging(tmp_path_factory, monkeypatch):
    """Give manageProject a real logger without touching the user's log dir."""
    logDir = tmp_path_factory.mktemp("omp-logs")
    setApplication("testOmp", logDir=logDir)
    manageProjectModule.logger = getLogger(includeConsole=False)

    # Entry points reset the application context. Keep those real log writes
    # inside the fixture too, instead of touching the developer's home directory.
    def applicationSet(name, logDir=None):
        # Tests that explicitly supply a temporary home still exercise the real
        # default-path contract; only the unmodified developer home is redirected.
        if logDir is None and Path.home() == developerHome:
            logDir = fixtureLogDir
        setApplication(name, logDir=logDir)

    fixtureLogDir = logDir
    developerHome = Path.home()
    for name in (
        "organiseMyProjects.agentCheck",
        "organiseMyProjects.agentSessions",
        "organiseMyProjects.manageProject",
        "organiseMyProjects.myBoard",
        "organiseMyProjects.runLinter",
        "syncAgentInstructions",
    ):
        module = sys.modules.get(name)
        if module is not None and hasattr(module, "setApplication"):
            monkeypatch.setattr(module, "setApplication", applicationSet)


@pytest.fixture
def testFilePath(tmp_path):
    file = tmp_path / "example.py"
    file.write_text("def greet(name):\n" "    return f'hello {name}'\n")
    return file  # return Path; str(file) if your code expects a string


@pytest.fixture
def tempDir():
    """Create a temporary directory for testing."""
    tempPath = Path(tempfile.mkdtemp())
    yield tempPath
    shutil.rmtree(tempPath)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing (snake_case alias)."""
    tempPath = Path(tempfile.mkdtemp())
    yield tempPath
    shutil.rmtree(tempPath)


@pytest.fixture
def sampleProjectName():
    """Sample project name for testing."""
    return "testProject"


@pytest.fixture
def sample_project_name():
    """Sample project name for testing (snake_case alias)."""
    return "testProject"


@pytest.fixture
def mockPythonFile(tempDir):
    """Create a sample Python file for testing the linter."""
    pythonFile = tempDir / "test_file.py"
    content = """
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
"""
    pythonFile.write_text(content)
    return pythonFile


@pytest.fixture
def mockQtFile(tempDir):
    """Create a sample Qt/PySide6 Python file for testing the linter."""
    qtFile = tempDir / "test_qtFile.py"
    content = """
from PySide6.QtWidgets import QWidget, QPushButton, QLabel

class TestWidget(QWidget):
    def __init__(self):
        self.save_button = QPushButton()  # Valid snake_case
        self.title_label = QLabel()  # Valid snake_case
        self.invalidButton = QPushButton()  # Invalid - not snake_case
        self._internal_widget = QWidget()  # Valid - private member
"""
    qtFile.write_text(content)
    return qtFile
