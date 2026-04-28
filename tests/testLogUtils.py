"""
Tests for logUtils.py functionality.
"""

import datetime
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.logUtils import (
    _defaultLogDir,
    drawBox,
    getLogger,
    thisApplication,
)


class TestDefaultLogDir:
    """Test that the default log directory is ~/.local/state."""

    def testDefaultLogDirIsLocalState(self):
        """Test that _defaultLogDir returns ~/.local/state base directory."""
        expected = Path.home() / ".local" / "state"
        assert _defaultLogDir() == expected

    def testGetLoggerCreatesNameSubdirAndDateFile(self, tmp_path, monkeypatch):
        """Test that getLogger uses applicationLogDir/{name}-{date}.log when name matches the application context."""
        import organiseMyProjects.logUtils as logUtils
        appName = "testAppName"
        appLogDir = tmp_path / appName
        appLogDir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(logUtils, "thisApplication", appName)
        monkeypatch.setattr(logUtils, "_applicationLogDir", appLogDir)
        logger = getLogger(appName)
        expectedDate = datetime.date.today().isoformat()
        expectedFile = appLogDir / f"{appName}-{expectedDate}.log"
        assert expectedFile.exists(), f"Expected log file {expectedFile} was not created"


class TestDrawBox:

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
        assert (
            len(widths) == 1
        ), f"All lines should have equal width, got widths: {widths}"

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


class TestGetLoggerDryRun:
    """Test that getLogger() respects the dryRun parameter."""

    def testGetLoggerDryRunTrueReturnsAdapter(self, tmp_path):
        """Test that getLogger with dryRun=True returns a LoggerAdapter."""
        logger = getLogger("testDryRun", logDir=tmp_path, dryRun=True)
        assert isinstance(logger, logging.LoggerAdapter)

    def testGetLoggerDryRunFalseReturnsAdapter(self, tmp_path):
        """Test that getLogger with dryRun=False also returns a LoggerAdapter."""
        logger = getLogger("testLive", logDir=tmp_path, dryRun=False)
        assert isinstance(logger, logging.LoggerAdapter)

    def testGetLoggerDryRunDefaultReturnsAdapter(self, tmp_path):
        """Test that getLogger without dryRun returns a LoggerAdapter."""
        logger = getLogger("testDefault2", logDir=tmp_path)
        assert isinstance(logger, logging.LoggerAdapter)

    def testGetLoggerDryRunPrefixApplied(self, tmp_path):
        """Test that a logger from getLogger(dryRun=True) prefixes action() messages."""
        logger = getLogger("testDryRunPrefix", logDir=tmp_path, dryRun=True)
        records: list[logging.LogRecord] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        logger.logger.addHandler(_Capture())
        logger.action("moving file")
        assert records and "[] moving file" in records[0].getMessage()

    def testGetLoggerLiveNoPrefixApplied(self, tmp_path):
        """Test that a logger from getLogger(dryRun=False) does not add dryRun prefix."""
        logger = getLogger("testLivePrefix", logDir=tmp_path, dryRun=False)
        records: list[logging.LogRecord] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        logger.logger.addHandler(_Capture())
        logger.info("moving file")
        assert records and records[0].getMessage() == "...moving file"


class TestSemanticLogMethods:
    """Test the semantic log methods: doing, done, info, value."""

    def _captureRecords(self, logger):
        records: list[logging.LogRecord] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        logger.logger.addHandler(_Capture())
        return records

    def testInfoAddsEllipsisPrefix(self, tmp_path):
        """Test that info() prepends '...' to the message."""
        logger = getLogger("testInfoEllipsis", logDir=tmp_path)
        records = self._captureRecords(logger)
        logger.info("some message")
        assert records and records[0].getMessage() == "...some message"

    def testDoingAddsEllipsisSuffix(self, tmp_path):
        """Test that doing() appends '...' to the message."""
        logger = getLogger("testDoing", logDir=tmp_path)
        records = self._captureRecords(logger)
        logger.doing("processing files")
        assert records and records[0].getMessage() == "processing files..."

    def testDoneAddsEllipsisPrefix(self, tmp_path):
        """Test that done() prepends '...' to the message."""
        logger = getLogger("testDone", logDir=tmp_path)
        records = self._captureRecords(logger)
        logger.done("processing files")
        assert records and records[0].getMessage() == "...processing files"

    def testValueFormatsNameAndVariable(self, tmp_path):
        """Test that value() formats as '...message: variable'."""
        logger = getLogger("testValue", logDir=tmp_path)
        records = self._captureRecords(logger)
        logger.value("file count", 42)
        assert records and records[0].getMessage() == "...file count: 42"

    def testValueDryRunNoPrefix(self, tmp_path):
        """Test that value() does not insert dry-run prefix even when dryRun=True."""
        logger = getLogger("testValueDry", logDir=tmp_path, dryRun=True)
        records = self._captureRecords(logger)
        logger.value("file count", 42)
        assert records and records[0].getMessage() == "...file count: 42"

    def testInfoDryRunNoPrefix(self, tmp_path):
        """Test that info() does not insert dry-run prefix even when dryRun=True."""
        logger = getLogger("testInfoDry", logDir=tmp_path, dryRun=True)
        records = self._captureRecords(logger)
        logger.info("moving file")
        assert records and records[0].getMessage() == "...moving file"

    def testDoingDryRunNoPrefix(self, tmp_path):
        """Test that doing() does not insert dry-run prefix even when dryRun=True."""
        logger = getLogger("testDoingDry", logDir=tmp_path, dryRun=True)
        records = self._captureRecords(logger)
        logger.doing("processing files")
        assert records and records[0].getMessage() == "processing files..."

    def testDoneDryRunNoPrefix(self, tmp_path):
        """Test that done() does not insert dry-run prefix even when dryRun=True."""
        logger = getLogger("testDoneDry", logDir=tmp_path, dryRun=True)
        records = self._captureRecords(logger)
        logger.done("processing files")
        assert records and records[0].getMessage() == "...processing files"

    def testActionDryRunPrefixInserted(self, tmp_path):
        """Test that action() inserts '[] ' prefix when dryRun=True."""
        logger = getLogger("testActionDry", logDir=tmp_path, dryRun=True)
        records = self._captureRecords(logger)
        logger.action("moving file")
        assert records and records[0].getMessage() == "[] moving file..."

    def testActionLiveNoPrefixInserted(self, tmp_path):
        """Test that action() does not insert '[] ' prefix when dryRun=False."""
        logger = getLogger("testActionLive", logDir=tmp_path, dryRun=False)
        records = self._captureRecords(logger)
        logger.action("moving file")
        assert records and records[0].getMessage() == "moving file..."
