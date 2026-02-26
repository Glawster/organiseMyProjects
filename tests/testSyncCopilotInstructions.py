"""
Tests for syncCopilotInstructions.py
"""
import base64
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure repo root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import syncCopilotInstructions as sci


class TestBuildTargetContent:
    """Tests for buildTargetContent."""

    def testPrependsSyncComment(self):
        """Sync comment should be prepended to source content."""
        result = sci.buildTargetContent("# Title\n\nBody text.\n")
        assert result.startswith(sci.SYNC_COMMENT)

    def testSourceContentPreserved(self):
        """Original source content should appear after the sync comment."""
        source = "# Title\n\nBody text.\n"
        result = sci.buildTargetContent(source)
        assert result.endswith(source)


class TestBuildHeaders:
    """Tests for buildHeaders."""

    def testContainsAuthorization(self):
        """Authorization header should contain the token."""
        headers = sci.buildHeaders("mytoken")
        assert headers["Authorization"] == "token mytoken"

    def testContainsAcceptHeader(self):
        """Accept header should be set for GitHub API."""
        headers = sci.buildHeaders("tok")
        assert "github" in headers["Accept"].lower()


class TestGetRemoteFile:
    """Tests for getRemoteFile."""

    def testReturnsNoneOn404(self):
        """Should return None when the file does not exist."""
        mockResp = MagicMock()
        mockResp.status_code = 404
        with patch("syncCopilotInstructions.requests.get", return_value=mockResp):
            result = sci.getRemoteFile("owner/repo", ".github/file.md", {})
        assert result is None

    def testReturnsJsonOn200(self):
        """Should return parsed JSON on success."""
        mockResp = MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {"sha": "abc123", "content": "aGVsbG8="}
        mockResp.raise_for_status = MagicMock()
        with patch("syncCopilotInstructions.requests.get", return_value=mockResp):
            result = sci.getRemoteFile("owner/repo", ".github/file.md", {})
        assert result == {"sha": "abc123", "content": "aGVsbG8="}

    def testRaisesOnApiError(self):
        """Should raise HTTPError for non-404 error responses."""
        import requests as req

        mockResp = MagicMock()
        mockResp.status_code = 500
        mockResp.raise_for_status.side_effect = req.HTTPError("500 Server Error")
        with patch("syncCopilotInstructions.requests.get", return_value=mockResp):
            with pytest.raises(req.HTTPError):
                sci.getRemoteFile("owner/repo", ".github/file.md", {})


class TestSyncRepo:
    """Tests for syncRepo."""

    def _makeLogger(self):
        logger = MagicMock()
        return logger

    def testSkipsWhenContentMatches(self):
        """Should return 'skipped' when remote content matches target."""
        targetContent = "hello world"
        encodedContent = base64.b64encode(targetContent.encode()).decode()
        remoteData = {"sha": "abc", "content": encodedContent + "\n"}

        with patch("syncCopilotInstructions.getRemoteFile", return_value=remoteData):
            result = sci.syncRepo(
                "owner/repo", targetContent, True, {}, self._makeLogger(), False
            )
        assert result == "skipped"

    def testDryRunDoesNotCallPut(self):
        """In dry-run mode, putRemoteFile should NOT be called."""
        targetContent = "new content"
        encodedContent = base64.b64encode(b"old content").decode()
        remoteData = {"sha": "abc", "content": encodedContent}

        with patch("syncCopilotInstructions.getRemoteFile", return_value=remoteData):
            with patch("syncCopilotInstructions.putRemoteFile") as mockPut:
                result = sci.syncRepo(
                    "owner/repo", targetContent, True, {}, self._makeLogger(), False
                )

        mockPut.assert_not_called()
        assert result == "updated"

    def testConfirmCallsPut(self):
        """In confirm mode, putRemoteFile should be called."""
        targetContent = "new content"
        encodedContent = base64.b64encode(b"old content").decode()
        remoteData = {"sha": "abc", "content": encodedContent}

        with patch("syncCopilotInstructions.getRemoteFile", return_value=remoteData):
            with patch("syncCopilotInstructions.putRemoteFile") as mockPut:
                result = sci.syncRepo(
                    "owner/repo", targetContent, False, {}, self._makeLogger(), False
                )

        mockPut.assert_called_once()
        assert result == "updated"

    def testHandlesHttpError(self):
        """Should return 'failed' when an HTTPError is raised."""
        import requests as req

        with patch(
            "syncCopilotInstructions.getRemoteFile",
            side_effect=req.HTTPError("403 Forbidden"),
        ):
            result = sci.syncRepo(
                "owner/repo", "content", True, {}, self._makeLogger(), False
            )
        assert result == "failed"

    def testHandlesNetworkError(self):
        """Should return 'failed' on a network/connection error."""
        import requests as req

        with patch(
            "syncCopilotInstructions.getRemoteFile",
            side_effect=req.ConnectionError("timeout"),
        ):
            result = sci.syncRepo(
                "owner/repo", "content", True, {}, self._makeLogger(), False
            )
        assert result == "failed"

    def testCreatesFileWhenNotFound(self):
        """Should call putRemoteFile with sha=None when file doesn't exist."""
        targetContent = "new content"

        with patch("syncCopilotInstructions.getRemoteFile", return_value=None):
            with patch("syncCopilotInstructions.putRemoteFile") as mockPut:
                sci.syncRepo(
                    "owner/repo", targetContent, False, {}, self._makeLogger(), False
                )

        args, kwargs = mockPut.call_args
        # sha argument (index 3) should be None
        assert args[3] is None
