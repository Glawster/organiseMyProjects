"""
Tests for logUtils.py functionality.
"""
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.logUtils import DryRunLogger, drawBox, dryRunLog, getLogger


class TestDrawBox:
    """Test cases for the drawBox function."""

    def testDrawBoxSingleLine(self, capsys):
        """Test that a single-line message produces a correctly structured box."""
        drawBox("Hello World")

        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        # Should produce exactly 3 lines: top border, content, bottom border
        assert len(lines) == 3
        assert lines[0] == lines[2], "Top and bottom borders should be identical"
        assert "Hello World" in lines[1]
        assert lines[1].startswith("│")
        assert lines[1].endswith("│")

    def testDrawBoxMultiLine(self, capsys):
        """Test that a multi-line message produces the correct number of output lines."""
        drawBox("Line one\nLine two\nLine three")

        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        # Should produce: top border + 3 content lines + bottom border = 5 lines
        assert len(lines) == 5
        assert "Line one" in lines[1]
        assert "Line two" in lines[2]
        assert "Line three" in lines[3]

    def testDrawBoxEmptyMessage(self, capsys):
        """Test that an empty message is replaced with '(empty message)'."""
        drawBox("")

        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        assert len(lines) == 3
        assert "(empty message)" in lines[1]

    def testDrawBoxBorderWidth(self, capsys):
        """Test that the box width matches the message length plus padding."""
        message = "Test"
        padding = 2
        drawBox(message, padding=padding)

        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        # inner width = len(message) + padding * 2 = 4 + 4 = 8
        # border line = corner + 8 border chars + corner = 10 chars
        expectedBorderLen = 1 + len(message) + padding * 2 + 1
        assert len(lines[0]) == expectedBorderLen

    def testDrawBoxCustomChars(self, capsys):
        """Test that custom border, corner, and side characters are used."""
        drawBox("Test", border_char="-", corner_char="*", side_char="|")

        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        assert lines[0].startswith("*")
        assert lines[0].endswith("*")
        assert "-" in lines[0]
        assert lines[1].startswith("|")
        assert lines[1].endswith("|")

    def testDrawBoxAllLinesEqualWidth(self, capsys):
        """Test that all output lines have the same width."""
        drawBox("Short\nA much longer line here\nMid")

        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        widths = {len(line) for line in lines}
        assert len(widths) == 1, f"All lines should have equal width, got widths: {widths}"

    def testDrawBoxWithLogger(self):
        """Test that when a logger is provided, output goes to it instead of stdout."""
        mockLogger = MagicMock(spec=logging.Logger)

        drawBox("Log this message", logger=mockLogger)

        assert mockLogger.info.called
        callArgs = [call.args[0] for call in mockLogger.info.call_args_list]
        assert any("Log this message" in arg for arg in callArgs)
        # Should have exactly 3 calls: top border, content line, bottom border
        assert mockLogger.info.call_count == 3

    def testDrawBoxWithLoggerMultiLine(self):
        """Test that multi-line messages log all lines via logger."""
        mockLogger = MagicMock(spec=logging.Logger)

        drawBox("First line\nSecond line", logger=mockLogger)

        # 4 calls: top border + 2 content lines + bottom border
        assert mockLogger.info.call_count == 4

    def testDrawBoxNoPrintWhenLogger(self, capsys):
        """Test that nothing is printed to stdout when a logger is provided."""
        mockLogger = MagicMock(spec=logging.Logger)

        drawBox("Silent message", logger=mockLogger)

        captured = capsys.readouterr()
        assert captured.out == ""

    def testDrawBoxCustomPadding(self, capsys):
        """Test that custom padding is correctly applied."""
        message = "X"
        drawBox(message, padding=4)

        captured = capsys.readouterr()
        lines = captured.out.splitlines()

        # Inner width = 1 + 4*2 = 9; border = corner + 9 chars + corner = 11
        assert len(lines[0]) == 1 + len(message) + 4 * 2 + 1
        # Content line should have 4 spaces of padding on each side
        assert lines[1] == "│    X    │"


class TestDryRunLog:
    """Test cases for the dryRunLog() helper function."""

    def testDryRunLogWithDryRunTrue(self):
        """Test that dryRunLog prefixes the message when dryRun=True."""
        mockLogger = MagicMock(spec=logging.Logger)
        dryRunLog(mockLogger, "moving file", dryRun=True)
        mockLogger.info.assert_called_once_with("[DRY RUN] moving file")

    def testDryRunLogWithDryRunFalse(self):
        """Test that dryRunLog does not prefix the message when dryRun=False."""
        mockLogger = MagicMock(spec=logging.Logger)
        dryRunLog(mockLogger, "moving file", dryRun=False)
        mockLogger.info.assert_called_once_with("moving file")

    def testDryRunLogDefaultIsFalse(self):
        """Test that the default dryRun value is False (no prefix)."""
        mockLogger = MagicMock(spec=logging.Logger)
        dryRunLog(mockLogger, "moving file")
        mockLogger.info.assert_called_once_with("moving file")


class TestDryRunLogger:
    """Test cases for the DryRunLogger class."""

    def testInfoWithDryRunTrue(self):
        """Test that info() prefixes the message when dryRun=True."""
        mockLogger = MagicMock(spec=logging.Logger)
        drl = DryRunLogger(mockLogger, dryRun=True)
        drl.info("processing item")
        mockLogger.info.assert_called_once_with("[DRY RUN] processing item")

    def testInfoWithDryRunFalse(self):
        """Test that info() does not prefix the message when dryRun=False."""
        mockLogger = MagicMock(spec=logging.Logger)
        drl = DryRunLogger(mockLogger, dryRun=False)
        drl.info("processing item")
        mockLogger.info.assert_called_once_with("processing item")

    def testWarningWithDryRunTrue(self):
        """Test that warning() prefixes the message when dryRun=True."""
        mockLogger = MagicMock(spec=logging.Logger)
        drl = DryRunLogger(mockLogger, dryRun=True)
        drl.warning("skipping file")
        mockLogger.warning.assert_called_once_with("[DRY RUN] skipping file")

    def testWarningWithDryRunFalse(self):
        """Test that warning() does not prefix the message when dryRun=False."""
        mockLogger = MagicMock(spec=logging.Logger)
        drl = DryRunLogger(mockLogger, dryRun=False)
        drl.warning("skipping file")
        mockLogger.warning.assert_called_once_with("skipping file")

    def testErrorWithDryRunTrue(self):
        """Test that error() prefixes the message when dryRun=True."""
        mockLogger = MagicMock(spec=logging.Logger)
        drl = DryRunLogger(mockLogger, dryRun=True)
        drl.error("unexpected condition")
        mockLogger.error.assert_called_once_with("[DRY RUN] unexpected condition")

    def testErrorWithDryRunFalse(self):
        """Test that error() does not prefix the message when dryRun=False."""
        mockLogger = MagicMock(spec=logging.Logger)
        drl = DryRunLogger(mockLogger, dryRun=False)
        drl.error("unexpected condition")
        mockLogger.error.assert_called_once_with("unexpected condition")

    def testDefaultDryRunIsFalse(self):
        """Test that the default dryRun is False (no prefix)."""
        mockLogger = MagicMock(spec=logging.Logger)
        drl = DryRunLogger(mockLogger)
        drl.info("default behaviour")
        mockLogger.info.assert_called_once_with("default behaviour")


class TestGetLoggerDryRun:
    """Test that getLogger() respects the dryRun parameter."""

    def testGetLoggerDryRunTrueReturnsDryRunLogger(self, tmp_path):
        """Test that getLogger with dryRun=True returns a DryRunLogger."""
        logger = getLogger("testDryRun", logDir=tmp_path, dryRun=True)
        assert isinstance(logger, DryRunLogger)

    def testGetLoggerDryRunFalseReturnsStandardLogger(self, tmp_path):
        """Test that getLogger with dryRun=False returns a standard Logger."""
        logger = getLogger("testLive", logDir=tmp_path, dryRun=False)
        assert isinstance(logger, logging.Logger)

    def testGetLoggerDryRunDefaultReturnsStandardLogger(self, tmp_path):
        """Test that getLogger without dryRun returns a standard Logger."""
        logger = getLogger("testDefault", logDir=tmp_path)
        assert isinstance(logger, logging.Logger)
