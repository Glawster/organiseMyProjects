"""
Tests for syncAgentInstructions.py
"""

import base64
import json
import stat
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure repo root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import syncAgentInstructions as sci


class TestConfigToken:
    """Tests for persistent GitHub token configuration."""

    def testLoadsStoredToken(self, tmp_path):
        """The token should be read from the JSON config store."""
        configPath = tmp_path / "sync.json"
        configPath.write_text(json.dumps({"githubToken": "stored-token"}))

        assert sci.configLoadToken(configPath) == "stored-token"

    def testMissingOrInvalidConfigReturnsEmptyToken(self, tmp_path):
        """A missing or malformed store should not crash token resolution."""
        configPath = tmp_path / "sync.json"
        assert sci.configLoadToken(configPath) == ""

        configPath.write_text("not json")
        assert sci.configLoadToken(configPath) == ""

    def testSavesTokenWithPrivatePermissions(self, tmp_path):
        """Saved credentials should only be readable by the current user."""
        configPath = tmp_path / "config" / "sync.json"

        sci.configSaveToken("new-token", configPath)

        assert json.loads(configPath.read_text()) == {"githubToken": "new-token"}
        assert stat.S_IMODE(configPath.stat().st_mode) == 0o600


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


class TestSyncSpecs:
    """Tests for sync file configuration."""

    def testIncludesAgentsFile(self):
        """AGENTS.md should be part of files synced to target repos."""
        targetPaths = [spec["targetPath"] for spec in sci.SYNC_SPECS]
        assert "AGENTS.md" in targetPaths

    def testIncludesCopilotCompatibilityFile(self):
        """Copilot's standard repository instruction path should be synced."""
        targetPaths = [spec["targetPath"] for spec in sci.SYNC_SPECS]
        assert ".github/copilot-instructions.md" in targetPaths

    def testCopilotSpecUsesCopilotSource(self):
        """The Copilot shim should be synced from its dedicated source file."""
        specsByTarget = {spec["targetPath"]: spec for spec in sci.SYNC_SPECS}
        copilotSpec = specsByTarget[".github/copilot-instructions.md"]
        assert copilotSpec["sourceFile"].name == "copilot-instructions.md"

    def testIncludesClaudeShim(self):
        """The Claude Code instruction pointer shim should be synced."""
        specsByTarget = {spec["targetPath"]: spec for spec in sci.SYNC_SPECS}
        claudeSpec = specsByTarget["CLAUDE.md"]
        assert claudeSpec["sourceFile"].name == "CLAUDE.md"

    def testCheckedInCopilotFilePointsToCanonicalAgentInstructions(self):
        """The repository's copilot shim should point to agent-instructions.md."""
        repoRoot = Path(__file__).parent.parent
        copilotContent = (repoRoot / ".github" / "copilot-instructions.md").read_text()
        assert "agent-instructions.md" in copilotContent

    def testIncludesRepositoryLayout(self):
        """The shared repository layout should be synced as documentation."""
        specsByTarget = {spec["targetPath"]: spec for spec in sci.SYNC_SPECS}
        layoutSpec = specsByTarget[".github/repositoryLayout.md"]
        assert layoutSpec["sourceFile"].name == "repositoryLayout.md"

    def testIncludesRequirementsManagement(self):
        """The shared requirements guide should be synced as documentation."""
        specsByTarget = {spec["targetPath"]: spec for spec in sci.SYNC_SPECS}
        guideSpec = specsByTarget[".github/requirementsManagement.md"]
        assert guideSpec["sourceFile"].name == "requirementsManagement.md"

    def testIncludesHowToRelease(self):
        """The shared release guide should be synced as documentation."""
        specsByTarget = {spec["targetPath"]: spec for spec in sci.SYNC_SPECS}
        releaseSpec = specsByTarget[".github/howToRelease.md"]
        assert releaseSpec["sourceFile"].name == "howToRelease.md"


class TestGetRemoteFile:
    """Tests for getRemoteFile."""

    def testReturnsNoneOn404(self):
        """Should return None when the file does not exist."""
        mockResp = MagicMock()
        mockResp.status_code = 404
        with patch("syncAgentInstructions.requests.get", return_value=mockResp):
            result = sci.getRemoteFile("owner/repo", ".github/file.md", {})
        assert result is None

    def testReturnsJsonOn200(self):
        """Should return parsed JSON on success."""
        mockResp = MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {"sha": "abc123", "content": "aGVsbG8="}
        mockResp.raise_for_status = MagicMock()
        with patch("syncAgentInstructions.requests.get", return_value=mockResp):
            result = sci.getRemoteFile("owner/repo", ".github/file.md", {})
        assert result == {"sha": "abc123", "content": "aGVsbG8="}

    def testRaisesOnApiError(self):
        """Should raise HTTPError for non-404 error responses."""
        import requests as req

        mockResp = MagicMock()
        mockResp.status_code = 500
        mockResp.raise_for_status.side_effect = req.HTTPError("500 Server Error")
        with patch("syncAgentInstructions.requests.get", return_value=mockResp):
            with pytest.raises(req.HTTPError):
                sci.getRemoteFile("owner/repo", ".github/file.md", {})


class TestGetTargetRepos:
    """Tests for dynamic target repository discovery."""

    @staticmethod
    def _repo(
        name: str,
        owner: str = "Glawster",
        archived: bool = False,
        fork: bool = False,
    ) -> dict:
        return {
            "full_name": f"{owner}/{name}",
            "owner": {"login": owner},
            "archived": archived,
            "fork": fork,
        }

    def testFiltersAndSortsEligibleRepos(self):
        """Only active, owned, non-source, non-fork repos should be returned."""
        response = MagicMock()
        response.json.return_value = [
            self._repo("zebra"),
            self._repo("Alpha"),
            self._repo("organiseMyProjects"),
            self._repo("archived", archived=True),
            self._repo("forked", fork=True),
            self._repo("external", owner="someoneElse"),
        ]

        with patch("syncAgentInstructions.requests.get", return_value=response):
            result = sci.getTargetRepos({})

        assert result == ["Glawster/Alpha", "Glawster/zebra"]
        response.raise_for_status.assert_called_once()

    def testFetchesAllPages(self):
        """A full API page should cause the next page to be requested."""
        firstPage = MagicMock()
        firstPage.json.return_value = [self._repo(f"repo{index}") for index in range(100)]
        secondPage = MagicMock()
        secondPage.json.return_value = [self._repo("finalRepo")]

        with patch(
            "syncAgentInstructions.requests.get",
            side_effect=[firstPage, secondPage],
        ) as mockGet:
            result = sci.getTargetRepos({})

        assert len(result) == 101
        assert mockGet.call_args_list[1].kwargs["params"]["page"] == 2


class TestRepoSelect:
    """Tests for selecting all or one target repository."""

    repos = ["Glawster/Alpha", "Glawster/Beta", "Glawster/Gamma"]

    def testReturnsAllReposByDefault(self):
        """Omitting --repo should preserve the existing all-repo behavior."""
        assert sci.repoSelect(self.repos, None) == self.repos

    @pytest.mark.parametrize("requested", ["Beta", "glawster/beta"])
    def testSelectsNamedRepo(self, requested):
        """A repository may be selected by short or full case-insensitive name."""
        assert sci.repoSelect(self.repos, requested) == ["Glawster/Beta"]

    def testSelectsRepoByNumber(self, capsys):
        """An empty --repo value should show and use the numbered selector."""
        with patch("builtins.input", return_value="2"):
            result = sci.repoSelect(self.repos, "")

        assert result == ["Glawster/Beta"]
        output = capsys.readouterr().out
        assert "1. Glawster/Alpha" in output
        assert "3. Glawster/Gamma" in output

    def testRetriesInvalidNumber(self, capsys):
        """The selector should retry until the number is in range."""
        with patch("builtins.input", side_effect=["wrong", "9", "1"]):
            result = sci.repoSelect(self.repos, "")

        assert result == ["Glawster/Alpha"]
        assert capsys.readouterr().out.count("Enter a number from 1 to 3.") == 2

    def testRejectsUnknownRepo(self):
        """A named repository must be in the eligible repository list."""
        with pytest.raises(ValueError, match="not eligible or was not found"):
            sci.repoSelect(self.repos, "Missing")

    def testRejectsEmptyRepoList(self):
        """Interactive selection should fail clearly when no repos are eligible."""
        with pytest.raises(ValueError, match="No eligible repositories"):
            sci.repoSelect([], "")


class TestSyncPullRequest:
    """Tests for the pull request merge workflow."""

    def testCreatesAndMergesPullRequest(self):
        """A missing pull request should be created and merged."""
        pullRequest = {"number": 42, "state": "open", "merged_at": None}
        with patch("syncAgentInstructions.getPullRequest", return_value=None):
            with patch(
                "syncAgentInstructions.createPullRequest",
                return_value=pullRequest,
            ) as mockCreate:
                with patch(
                    "syncAgentInstructions.mergePullRequest",
                    return_value="merged",
                ) as mockMerge:
                    result = sci.syncPullRequest(
                        "owner/repo", "sync/branch", "main", {}
                    )

        assert result == ("merged", 42)
        mockCreate.assert_called_once()
        mockMerge.assert_called_once_with("owner/repo", 42, {})

    def testReusesOpenPullRequest(self):
        """An existing open pull request should not be duplicated."""
        pullRequest = {"number": 7, "state": "open", "merged_at": None}
        with patch("syncAgentInstructions.getPullRequest", return_value=pullRequest):
            with patch("syncAgentInstructions.createPullRequest") as mockCreate:
                with patch(
                    "syncAgentInstructions.mergePullRequest",
                    return_value="conflict",
                ):
                    result = sci.syncPullRequest(
                        "owner/repo", "sync/branch", "main", {}
                    )

        assert result == ("conflict", 7)
        mockCreate.assert_not_called()

    def testReportsAlreadyMergedPullRequest(self):
        """An already merged pull request should not be recreated."""
        pullRequest = {
            "number": 8,
            "state": "closed",
            "merged_at": "2026-07-22T12:00:00Z",
        }
        with patch("syncAgentInstructions.getPullRequest", return_value=pullRequest):
            result = sci.syncPullRequest("owner/repo", "sync/branch", "main", {})

        assert result == ("already_merged", 8)

    def testReturnsFailedOnApiError(self):
        """Unexpected GitHub errors should be reported as failures."""
        import requests as req

        with patch(
            "syncAgentInstructions.getPullRequest",
            side_effect=req.HTTPError("server error"),
        ):
            result = sci.syncPullRequest("owner/repo", "sync/branch", "main", {})

        assert result == ("failed", None)


class TestMergePullRequest:
    """Tests for mergePullRequest."""

    @pytest.mark.parametrize("statusCode", [405, 409])
    def testReportsPullRequestRequiringReview(self, statusCode):
        """Blocked and conflicting pull requests should require review."""
        mockResp = MagicMock(status_code=statusCode)
        with patch("syncAgentInstructions.requests.put", return_value=mockResp):
            result = sci.mergePullRequest("owner/repo", 42, {})

        assert result == "conflict"

    def testReportsSuccessfulMerge(self):
        """A successfully merged pull request should be reported."""
        mockResp = MagicMock(status_code=200)
        mockResp.json.return_value = {"merged": True}
        with patch("syncAgentInstructions.requests.put", return_value=mockResp):
            result = sci.mergePullRequest("owner/repo", 42, {})

        assert result == "merged"


class TestSyncRepo:
    """Tests for syncRepo."""

    def _makeLogger(self):
        logger = MagicMock()
        return logger

    def testSkipsWhenContentMatches(self):
        """Should skip when content on the default branch matches."""
        targetContent = "hello world"
        encodedContent = base64.b64encode(targetContent.encode()).decode()
        remoteData = {"sha": "abc", "content": encodedContent + "\n"}

        with patch("syncAgentInstructions.getRemoteFile", return_value=remoteData):
            result = sci.syncRepo(
                "owner/repo",
                ".github/agent-instructions.md",
                targetContent,
                "sync: update instructions",
                True,
                {},
                self._makeLogger(),
                False,
            )
        assert result == "skipped"

    def testReadyWhenSyncBranchContentMatches(self):
        """A matching existing sync branch should remain eligible to merge."""
        targetContent = "hello world"
        encodedContent = base64.b64encode(targetContent.encode()).decode()
        remoteData = {"sha": "abc", "content": encodedContent}

        with patch("syncAgentInstructions.getRemoteFile", return_value=remoteData):
            result = sci.syncRepo(
                "owner/repo",
                ".github/agent-instructions.md",
                targetContent,
                "sync: update instructions",
                False,
                {},
                self._makeLogger(),
                False,
                branch="sync/instructions-20260722",
            )

        assert result == "ready"

    def testDryRunDoesNotCallPut(self):
        """In dry-run mode, putRemoteFile should NOT be called."""
        targetContent = "new content"
        encodedContent = base64.b64encode(b"old content").decode()
        remoteData = {"sha": "abc", "content": encodedContent}

        with patch("syncAgentInstructions.getRemoteFile", return_value=remoteData):
            with patch("syncAgentInstructions.putRemoteFile") as mockPut:
                result = sci.syncRepo(
                    "owner/repo",
                    ".github/agent-instructions.md",
                    targetContent,
                    "sync: update instructions",
                    True,
                    {},
                    self._makeLogger(),
                    False,
                )

        mockPut.assert_not_called()
        assert result == "updated"

    def testConfirmCallsPut(self):
        """In confirm mode, putRemoteFile should be called."""
        targetContent = "new content"
        encodedContent = base64.b64encode(b"old content").decode()
        remoteData = {"sha": "abc", "content": encodedContent}

        with patch("syncAgentInstructions.getRemoteFile", return_value=remoteData):
            with patch("syncAgentInstructions.putRemoteFile") as mockPut:
                result = sci.syncRepo(
                    "owner/repo",
                    ".github/agent-instructions.md",
                    targetContent,
                    "sync: update instructions",
                    False,
                    {},
                    self._makeLogger(),
                    False,
                )

        mockPut.assert_called_once()
        assert result == "updated"

    def testHandlesHttpError(self):
        """Should return 'failed' when an HTTPError is raised."""
        import requests as req

        with patch(
            "syncAgentInstructions.getRemoteFile",
            side_effect=req.HTTPError("403 Forbidden"),
        ):
            result = sci.syncRepo(
                "owner/repo",
                ".github/agent-instructions.md",
                "content",
                "sync: update instructions",
                True,
                {},
                self._makeLogger(),
                False,
            )
        assert result == "failed"

    def testHandlesNetworkError(self):
        """Should return 'failed' on a network/connection error."""
        import requests as req

        with patch(
            "syncAgentInstructions.getRemoteFile",
            side_effect=req.ConnectionError("timeout"),
        ):
            result = sci.syncRepo(
                "owner/repo",
                ".github/agent-instructions.md",
                "content",
                "sync: update instructions",
                True,
                {},
                self._makeLogger(),
                False,
            )
        assert result == "failed"

    def testCreatesFileWhenNotFound(self):
        """Should call putRemoteFile with sha=None when file doesn't exist."""
        targetContent = "new content"

        with patch("syncAgentInstructions.getRemoteFile", return_value=None):
            with patch("syncAgentInstructions.putRemoteFile") as mockPut:
                sci.syncRepo(
                    "owner/repo",
                    ".github/agent-instructions.md",
                    targetContent,
                    "sync: update instructions",
                    False,
                    {},
                    self._makeLogger(),
                    False,
                )

        args, kwargs = mockPut.call_args
        # sha argument (index 3) should be None
        assert args[3] is None

    def testPreparesOneBranchForMultipleFiles(self):
        """Multiple file updates in one repository should share one branch."""
        encodedContent = base64.b64encode(b"old content").decode()
        remoteData = {"sha": "abc", "content": encodedContent}
        preparedBranches = set()
        logger = self._makeLogger()

        with patch(
            "syncAgentInstructions.getRemoteFile", return_value=remoteData
        ), patch(
            "syncAgentInstructions.getDefaultBranch", return_value="main"
        ), patch(
            "syncAgentInstructions.getBranchHeadSha", return_value="head-sha"
        ), patch(
            "syncAgentInstructions.createBranch"
        ) as mockCreate, patch(
            "syncAgentInstructions.putRemoteFile"
        ):
            for targetPath in (".github/agent-instructions.md", "AGENTS.md"):
                result = sci.syncRepo(
                    "owner/repo",
                    targetPath,
                    "new content",
                    "sync: update instructions",
                    False,
                    {},
                    logger,
                    False,
                    branch="sync/instructions-20260722",
                    preparedBranches=preparedBranches,
                )
                assert result == "updated"

        mockCreate.assert_called_once_with(
            "owner/repo", "sync/instructions-20260722", "head-sha", {}
        )
        assert preparedBranches == {"owner/repo"}
        assert logger.action.call_args_list.count(
            (("prepare sync branch",), {})
        ) == 1
