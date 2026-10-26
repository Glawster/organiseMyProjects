"""
Tests for runLinter.py functionality.
"""

import os
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.guiNamingLinter import findingDescribe
from organiseMyProjects.runLinter import (
    lintTargetsCollect,
    lintTargetsDiscover,
    main,
)


class TestRunLinter:
    """Test cases for runLinter functionality."""

    def _mainExitCode(self, *args) -> int:
        with patch("sys.argv", ["runLinter.py", *args]):
            with pytest.raises(SystemExit) as exc:
                main()
        return exc.value.code

    def testFindingFormatDistinguishesSameBasename(self, tempDir, monkeypatch):
        """Requirement 013 criterion 1: relative path, line, rule ID, message."""
        for package in ("alpha", "beta"):
            (tempDir / package).mkdir()
            (tempDir / package / "__init__.py").write_text(
                "def bad_name():\n    pass\n"
            )
        monkeypatch.chdir(tempDir)

        result = lintTargetsCollect(["."])
        rendered = sorted(finding.render() for finding in result.findings)

        assert rendered == [
            f"alpha{os.sep}__init__.py:1: NAM-003 function 'bad_name' should be domainAction camelCase",
            f"beta{os.sep}__init__.py:1: NAM-003 function 'bad_name' should be domainAction camelCase",
        ]

    def testRuleSpecificMessages(self):
        """Criterion 2: non-naming rules do not use the generic naming template."""
        ruleId, message = findingDescribe(
            "line", "LOG-SEC-002: call line() immediately after the application header"
        )
        assert ruleId == "LOG-SEC-002"
        assert message == "call line() immediately after the application header"
        ruleId, message = findingDescribe("Already done", "Logging (info)")
        assert ruleId == "LOG-CASE-001"
        assert "should follow naming rule" not in message

    def testSummaryCountsFindingsFilesAndTime(self, tempDir, monkeypatch, capsys):
        """Criterion 3: summary reports findings, affected and passed files, time."""
        (tempDir / "good.py").write_text("VALUE = 1\n")
        (tempDir / "bad.py").write_text(
            "def bad_name():\n    pass\n\n\ndef worse():\n    pass\n"
        )
        monkeypatch.chdir(tempDir)

        assert self._mainExitCode(".") == 1
        summary = [
            row for row in capsys.readouterr().out.splitlines() if " in " in row
        ][-1]
        assert re.search(
            r"=+ 2 findings in 1 file, 1 file passed in \d+\.\d\ds =+", summary
        )

    def testProgressMarksPassedAndFailedFiles(self, tempDir, monkeypatch, capsys):
        (tempDir / "good.py").write_text("VALUE = 1\n")
        (tempDir / "bad.py").write_text("def bad_name():\n    pass\n")
        monkeypatch.chdir(tempDir)

        self._mainExitCode(".")
        output = capsys.readouterr().out.splitlines()
        assert "bad.py FAILED" in output
        assert "good.py PASSED" in output

    def testCleanProjectExitsZero(self, tempDir, monkeypatch, capsys):
        """Criterion 4."""
        (tempDir / "good.py").write_text("VALUE = 1\n")
        monkeypatch.chdir(tempDir)

        assert self._mainExitCode(".") == 0
        assert re.search(r"=+ 1 file passed in \d+\.\d\ds =+", capsys.readouterr().out)

    def testFindingsExitOne(self, testFilePath):
        """Criterion 5."""
        (testFilePath.parent / "bad.py").write_text("def bad_name():\n    pass\n")
        assert self._mainExitCode(str(testFilePath.parent / "bad.py")) == 1

    def testMainLintsSuppliedTarget(self, testFilePath):
        with patch("organiseMyProjects.runLinter._violationsFiltered") as mockLint:
            mockLint.return_value = []
            assert self._mainExitCode(str(testFilePath)) == 0
        mockLint.assert_called_once_with(str(testFilePath))

    def testMainNonexistentTarget(self, tempDir, capsys):
        """Criterion 6: missing target."""
        assert self._mainExitCode(str(tempDir / "nonexistent.py")) == 2
        assert "does not exist" in capsys.readouterr().out

    def testMainNonPythonTarget(self, tempDir, capsys):
        """Criterion 6: non-Python target."""
        textFile = tempDir / "readme.txt"
        textFile.write_text("This is not Python")
        assert self._mainExitCode(str(textFile)) == 2
        assert "not a Python file" in capsys.readouterr().out

    def testMainUnreadableTarget(self, tempDir, capsys):
        """Criterion 6: unreadable target."""
        pythonFile = tempDir / "test.py"
        pythonFile.write_text("# Python file")
        with patch("organiseMyProjects.runLinter.os.access", return_value=False):
            assert self._mainExitCode(str(pythonFile)) == 2
        assert "not readable" in capsys.readouterr().out

    def testTargetErrorTakesPrecedenceOverFindings(self, tempDir):
        bad = tempDir / "bad.py"
        bad.write_text("def bad_name():\n    pass\n")
        assert self._mainExitCode(str(bad), str(tempDir / "missing.py")) == 2

    def testNoPythonFilesExitsFive(self, tempDir, capsys):
        """Criterion 7."""
        (tempDir / "notes.txt").write_text("text")
        assert self._mainExitCode(str(tempDir)) == 5
        assert "no Python files linted" in capsys.readouterr().out

    def testUnparseableFileIsReportedAsFinding(self, tempDir):
        broken = tempDir / "broken.py"
        broken.write_text("def broken(:\n")
        result = lintTargetsCollect([str(broken)])
        assert [finding.ruleId for finding in result.findings] == ["LINT-001"]
        assert result.exitCode == 1

    def testMainNoTargetsLintsDiscoveredDirectories(self, tempDir, monkeypatch):
        """With no targets, discovered project directories are linted."""
        for name in ("src", "ui", "tests"):
            (tempDir / name).mkdir()
        monkeypatch.chdir(tempDir)

        with patch(
            "organiseMyProjects.runLinter.lintTargetsCollect",
            wraps=lintTargetsCollect,
        ) as mockCollect:
            self._mainExitCode()

        assert mockCollect.call_args.args[0] == ["src", "ui", "tests"]

    def testMainNoTargetsFallsBackToCurrentDirectory(self, tempDir, monkeypatch):
        monkeypatch.chdir(tempDir)

        with patch(
            "organiseMyProjects.runLinter.lintTargetsCollect",
            wraps=lintTargetsCollect,
        ) as mockCollect:
            assert self._mainExitCode() == 5

        assert mockCollect.call_args.args[0] == ["."]

    def testMainWithMarkupCheck(self):
        """Test running markup lint in check mode."""
        testArgs = ["runLinter.py", "--markup"]

        with patch("sys.argv", testArgs):
            with patch(
                "organiseMyProjects.runLinter.markupFix", return_value=0
            ) as mockMarkupFix:
                with patch(
                    "organiseMyProjects.runLinter.lintTargetsCollect"
                ) as mockLintGui:
                    with patch(
                        "organiseMyProjects.runLinter._violationsFiltered"
                    ) as mockLintFile:
                        main()

        mockMarkupFix.assert_called_once_with(targets=None, fix=False, strict=False)
        mockLintGui.assert_not_called()
        mockLintFile.assert_not_called()

    def testMainWithMarkupFix(self):
        """Test running markup lint in fix mode."""
        testArgs = ["runLinter.py", "--markup", "--fix"]

        with patch("sys.argv", testArgs):
            with patch(
                "organiseMyProjects.runLinter.markupFix", return_value=0
            ) as mockMarkupFix:
                with patch(
                    "organiseMyProjects.runLinter.lintTargetsCollect"
                ) as mockLintGui:
                    with patch(
                        "organiseMyProjects.runLinter._violationsFiltered"
                    ) as mockLintFile:
                        main()

        mockMarkupFix.assert_called_once_with(targets=None, fix=True, strict=False)
        mockLintGui.assert_not_called()
        mockLintFile.assert_not_called()

    def testMainWithMarkupStrict(self):
        """Test strict markup mode passes strict flag through to markupFix."""
        testArgs = ["runLinter.py", "--markup", "--strict"]

        with patch("sys.argv", testArgs):
            with patch(
                "organiseMyProjects.runLinter.markupFix", return_value=0
            ) as mockMarkupFix:
                main()

        mockMarkupFix.assert_called_once_with(targets=None, fix=False, strict=True)

    def testMainWithLegacyFixMarkupFlag(self):
        """Test legacy --fix-markup flag still works for compatibility."""
        testArgs = ["runLinter.py", "--fix-markup"]

        with patch("sys.argv", testArgs):
            with patch(
                "organiseMyProjects.runLinter.markupFix", return_value=0
            ) as mockMarkupFix:
                main()

        mockMarkupFix.assert_called_once_with(targets=None, fix=True, strict=False)

    def testMainWithMarkupTarget(self):
        """Test markup mode passes positional targets to markupFix."""
        testArgs = ["runLinter.py", "--markup", "README.md"]

        with patch("sys.argv", testArgs):
            with patch(
                "organiseMyProjects.runLinter.markupFix", return_value=0
            ) as mockMarkupFix:
                main()

        mockMarkupFix.assert_called_once_with(
            targets=["README.md"], fix=False, strict=False
        )

    def testMainMarkupFailureExits(self):
        """Test non-zero markup lint exit code propagates as CLI failure."""
        testArgs = ["runLinter.py", "--markup", "--fix"]

        with patch("sys.argv", testArgs):
            with patch("organiseMyProjects.runLinter.markupFix", return_value=1):
                with pytest.raises(SystemExit) as exc:
                    main()

        assert exc.value.code == 1

    def testMainFixWithoutMarkupFails(self):
        """Test --fix by itself is rejected to avoid ambiguous intent."""
        testArgs = ["runLinter.py", "--fix"]

        with patch("sys.argv", testArgs):
            with pytest.raises(SystemExit) as exc:
                main()

        assert exc.value.code == 2

    def testMainStrictWithoutMarkupFails(self):
        """Test --strict by itself is rejected because it only applies to markup mode."""
        testArgs = ["runLinter.py", "--strict"]

        with patch("sys.argv", testArgs):
            with pytest.raises(SystemExit) as exc:
                main()

        assert exc.value.code == 2


class TestLintTargetsDiscover:
    """Unit tests for default source-directory discovery."""

    def testConventionalSrcLayout(self, tempDir):
        (tempDir / "src").mkdir()
        (tempDir / "src" / "app.py").write_text("value = 1\n")

        assert lintTargetsDiscover(tempDir) == ["src"]

    def testRootLevelPackageMatchingRepositoryName(self, tempDir):
        packageDir = tempDir / tempDir.name
        packageDir.mkdir()
        (packageDir / "__init__.py").write_text("")

        assert tempDir.name in lintTargetsDiscover(tempDir)
        assert "." not in lintTargetsDiscover(tempDir)

    def testPyprojectPackagesFindWhere(self, tempDir):
        (tempDir / "lib").mkdir()
        (tempDir / "lib" / "pkg.py").write_text("value = 1\n")
        (tempDir / "pyproject.toml").write_text(
            '[tool.setuptools.packages.find]\nwhere = ["lib"]\n'
        )

        assert lintTargetsDiscover(tempDir) == ["lib"]

    def testPyprojectExplicitPackageList(self, tempDir):
        (tempDir / "footballVision").mkdir()
        (tempDir / "footballVision" / "__init__.py").write_text("")
        (tempDir / "pyproject.toml").write_text(
            "[project]\n"
            'name = "footballVision"\n\n'
            "[tool.setuptools]\n"
            'packages = ["footballVision"]\n'
        )

        assert lintTargetsDiscover(tempDir) == ["footballVision"]

    def testSourcePackagePlusTests(self, tempDir):
        (tempDir / "src").mkdir()
        (tempDir / "tests").mkdir()

        assert lintTargetsDiscover(tempDir) == ["src", "tests"]

    def testConfiguredSourcePathThatDoesNotExist(self, tempDir):
        (tempDir / "tests").mkdir()
        (tempDir / "pyproject.toml").write_text(
            '[tool.setuptools.packages.find]\nwhere = ["missingSrc"]\n'
        )

        assert lintTargetsDiscover(tempDir) == ["tests"]

    def testDuplicateDiscoveriesAreCollapsed(self, tempDir):
        (tempDir / "src").mkdir()
        (tempDir / "pyproject.toml").write_text(
            '[tool.setuptools.packages.find]\nwhere = ["src"]\n'
        )

        assert lintTargetsDiscover(tempDir) == ["src"]

    def testFallbackToCurrentDirectory(self, tempDir):
        (tempDir / "README.md").write_text("docs only\n")

        assert lintTargetsDiscover(tempDir) == ["."]

    def testExplicitTargetsBypassDiscovery(self, testFilePath):
        testArgs = ["runLinter.py", str(testFilePath)]

        with patch("sys.argv", testArgs):
            with patch(
                "organiseMyProjects.runLinter.lintTargetsDiscover"
            ) as mockDiscover:
                with patch(
                    "organiseMyProjects.runLinter._violationsFiltered"
                ) as mockLintFile:
                    mockLintFile.return_value = []
                    with pytest.raises(SystemExit):
                        main()
                    mockDiscover.assert_not_called()
                    mockLintFile.assert_called_once_with(str(testFilePath))


class TestIntegration:
    """Integration tests for the complete linting workflow."""

    def testFullLintingWorkflow(self, tempDir, capsys):
        """Test the complete linting workflow from command line to output."""
        # Create a Python file with various violations
        pythonFile = tempDir / "gui_test.py"
        content = """
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
"""
        pythonFile.write_text(content)

        # Run the linter
        testArgs = ["runLinter.py", str(pythonFile)]

        with patch("sys.argv", testArgs):
            with pytest.raises(SystemExit) as exc:
                main()

        captured = capsys.readouterr()

        # Verify that violations were detected, reported and enforced
        assert exc.value.code == 1
        assert "gui_test.py:" in captured.out
        assert "save_button" in captured.out or "status_label" in captured.out

    def testDirectoryLintingWorkflow(self, tempDir, capsys):
        """Test linting an entire directory structure."""
        # Create subdirectories
        srcDir = tempDir / "src"
        uiDir = tempDir / "ui"
        srcDir.mkdir()
        uiDir.mkdir()

        # Create Python files in subdirectories
        (srcDir / "utils.py").write_text("""
def good_function():
    pass
""")

        (uiDir / "main_frame.py").write_text("""
import tkinter as tk

class MainFrame:
    def __init__(self):
        self.btnClose = tk.Button()  # Good naming
        self.bad_button = tk.Button()  # Bad naming
""")

        # Run linter on directory
        testArgs = ["runLinter.py", str(tempDir)]

        with patch("sys.argv", testArgs):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()

        # Verify output identifies the target and each nested file
        assert f"targets: {tempDir}" in captured.out
        assert "utils.py" in captured.out
        assert "main_frame.py" in captured.out


def testCommandHeaderSeparator(tmp_path, monkeypatch, capsys):
    from organiseMyProjects import logUtils
    from organiseMyProjects.version import VERSION

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    target = tmp_path / "example.py"
    target.write_text("VALUE = 1\n")
    monkeypatch.setattr(sys, "argv", ["runLinter", str(target)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0

    output = capsys.readouterr().out.splitlines()
    assert output[:3] == ["", ">" + "-" * 80 + "<", ""]
    assert output[3:5] == [f"organiseMyProjects runLinter {VERSION}", "-" * 80]
    assert output.count(">" + "-" * 80 + "<") == 1
    logs = list(logUtils.getApplicationLogDir().glob("*.log"))
    assert len(logs) == 1
    assert "-" * 80 + "\n" in logs[0].read_text()
