#!/usr/bin/env python3
"""
syncCopilotInstructions.py

Syncs the canonical .github/copilot-instructions.md from organiseMyProjects
out to all other Glawster repos that use the shared template.

Default mode is dry-run; use --confirm to actually push changes.

This script always writes to a generated destination branch named:
sync/copilot-instructions-YYYYMMDD
"""

import argparse
import base64
import datetime
import os
import sys
from pathlib import Path
from typing import Optional

import requests

from organiseMyProjects.logUtils import getLogger, thisApplication

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCE_FILE = Path(__file__).resolve().parent / ".github" / "copilot-instructions.md"
TARGET_PATH = ".github/copilot-instructions.md"
COMMIT_MESSAGE = "sync: update copilot-instructions.md from organiseMyProjects template"
SYNC_COMMENT = (
    "<!-- synced from Glawster/organiseMyProjects -- do not edit directly -->\n"
)

# keep these in alphabetical order for easier maintenance
TARGET_REPOS = [
    "Glawster/organiseMyAlts",
    "Glawster/myDavinciScripts",
    "Glawster/organiseMyFooty",
    "Glawster/organiseMyPhotos",
    "Glawster/organiseMyVideo",
    "Glawster/b2-backup-scripts",
    "Glawster/batchImageProcessing",
    "Glawster/comfyuiWorkflows",
    "Glawster/createDirPerFile",
    "Glawster/directPayments",
    "Glawster/imageRecognition",
    "Glawster/linuxMigration",
    "Glawster/sidecarEditor",
    "Glawster/AbilityUsageTracker",
    "Glawster/OutdatedItemCleaner",
    "Glawster/wheresItAt",
]

API_BASE = "https://api.github.com"


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def buildHeaders(token: str) -> dict:
    """Return HTTP headers for the GitHub API."""
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def getRemoteFile(
    repo: str,
    path: str,
    headers: dict,
    ref: Optional[str] = None,
) -> Optional[dict]:
    """
    Fetch file metadata and content from the GitHub Contents API.

    Returns the parsed JSON response dict, or None if the file does not exist.
    Raises requests.HTTPError for unexpected API errors.
    """
    url = f"{API_BASE}/repos/{repo}/contents/{path}"
    params = {"ref": ref} if ref else None
    response = requests.get(url, headers=headers, params=params, timeout=15)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def getDefaultBranch(repo: str, headers: dict) -> str:
    """Return the destination repository default branch name."""
    url = f"{API_BASE}/repos/{repo}"
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()["default_branch"]


def getBranchHeadSha(repo: str, branch: str, headers: dict) -> str:
    """Return the head commit SHA for a branch."""
    url = f"{API_BASE}/repos/{repo}/git/ref/heads/{branch}"
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()["object"]["sha"]


def createBranch(repo: str, branch: str, sha: str, headers: dict) -> None:
    """Create a branch at sha, or no-op if it already exists."""
    url = f"{API_BASE}/repos/{repo}/git/refs"
    payload = {"ref": f"refs/heads/{branch}", "sha": sha}
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    if response.status_code == 422 and "Reference already exists" in response.text:
        return
    response.raise_for_status()


def putRemoteFile(
    repo: str,
    path: str,
    content: str,
    sha: Optional[str],
    commitMessage: str,
    headers: dict,
    branch: Optional[str] = None,
) -> None:
    """
    Create or update a file via the GitHub Contents API.

    content must be plain text; it will be base64-encoded before sending.
    sha is required when updating an existing file; pass None to create.
    """
    url = f"{API_BASE}/repos/{repo}/contents/{path}"
    payload: dict = {
        "message": commitMessage,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if sha:
        payload["sha"] = sha
    if branch:
        payload["branch"] = branch
    response = requests.put(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def buildTargetContent(sourceContent: str) -> str:
    """Return the content to write to each target repo (with sync comment prepended)."""
    return SYNC_COMMENT + sourceContent


def syncRepo(
    repo: str,
    targetContent: str,
    dryRun: bool,
    headers: dict,
    logger,
    verbose: bool,
    branch: Optional[str] = None,
) -> str:
    """
    Sync the copilot-instructions file to a single repo.

    Returns one of: "updated", "skipped", "failed".
    """
    logger.doing("checking repository")
    logger.value("repository", repo)

    try:
        # Try sync branch first if it exists (reuse branch from same day)
        remoteData = None
        if branch:
            logger.value("branch", branch)
            remoteData = getRemoteFile(repo, TARGET_PATH, headers, ref=branch)
            if remoteData is not None and verbose:
                logger.info("using existing branch")

        # If branch doesn't have the file, check default branch
        if remoteData is None:
            remoteData = getRemoteFile(repo, TARGET_PATH, headers, ref=None)

        if remoteData is not None:
            # Decode existing content
            remoteContent = base64.b64decode(remoteData["content"]).decode("utf-8")
            sha = remoteData["sha"]

            if remoteContent == targetContent:
                logger.info("already up to date, skipping")
                return "skipped"

            if verbose:
                logger.info("content differs, updating")
        else:
            sha = None
            if verbose:
                logger.info("file does not exist, creating")

        # Only create branch if update is needed
        if branch:
            defaultBranch = getDefaultBranch(repo, headers)
            defaultSha = getBranchHeadSha(repo, defaultBranch, headers)
            logger.action("create branch")
            if not dryRun:
                createBranch(repo, branch, defaultSha, headers)
                logger.done("create branch")

        logger.value("target path", TARGET_PATH)
        logger.action("update target file")
        if dryRun:
            return "updated"

        putRemoteFile(
            repo,
            TARGET_PATH,
            targetContent,
            sha,
            COMMIT_MESSAGE,
            headers,
            branch=branch,
        )
        logger.done("update target file")
        return "updated"

    except requests.HTTPError as exc:
        logger.error(f"Failed to sync {repo}: {exc}")
        return "failed"
    except requests.RequestException as exc:
        logger.error(f"Network error syncing {repo}: {exc}")
        return "failed"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse arguments and run the sync."""
    parser = argparse.ArgumentParser(
        description="Sync .github/copilot-instructions.md to all Glawster target repos."
    )
    parser.add_argument(
        "-y",
        "--confirm",
        action="store_true",
        help="execute the sync (default is dry-run)",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="GitHub PAT (overrides GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show detailed output for each repo",
    )
    args = parser.parse_args()

    dryRun = not args.confirm

    thisApplication = Path(__file__).stem
    logger = getLogger(thisApplication, includeConsole=True, dryRun=dryRun)
    logger.doing("starting")
    logger.value("dryRun", dryRun)

    syncBranch = f"sync/copilot-instructions-{datetime.date.today().strftime('%Y%m%d')}"
    logger.value("sync branch", syncBranch)

    # Resolve the GitHub token
    token = args.token or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.error("No GitHub token found. Set GITHUB_TOKEN or use --token.")
        sys.exit(1)

    # Read the source file
    if not SOURCE_FILE.exists():
        logger.error("Source file not found: %s", SOURCE_FILE)
        sys.exit(1)

    logger.value("source file", SOURCE_FILE)
    logger.value("target repo count", len(TARGET_REPOS))

    sourceContent = SOURCE_FILE.read_text(encoding="utf-8")
    targetContent = buildTargetContent(sourceContent)

    headers = buildHeaders(token)

    if dryRun:
        logger.info("dry-run mode: no changes will be made")

    counts = {"updated": 0, "skipped": 0, "failed": 0}

    for repo in TARGET_REPOS:
        result = syncRepo(
            repo,
            targetContent,
            dryRun,
            headers,
            logger,
            args.verbose,
            branch=syncBranch,
        )
        counts[result] += 1

    logger.info(
        "summary updated=%s skipped=%s failed=%s",
        counts["updated"],
        counts["skipped"],
        counts["failed"],
    )
    logger.done("finished")


if __name__ == "__main__":
    main()
