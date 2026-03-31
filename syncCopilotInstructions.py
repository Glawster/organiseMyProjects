#!/usr/bin/env python3
"""
syncCopilotInstructions.py

Syncs the canonical .github/copilot-instructions.md from organiseMyProjects
out to all other Glawster repos that use the shared template.

Default mode is dry-run; use --confirm to actually push changes.
"""

import argparse
import base64
import os
import sys
from pathlib import Path
from typing import Optional

import requests

from organiseMyProjects.logUtils import getLogger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCE_FILE = Path(__file__).resolve().parent / ".github" / "copilot-instructions.md"
TARGET_PATH = ".github/copilot-instructions.md"
COMMIT_MESSAGE = "sync: update copilot-instructions.md from organiseMyProjects template"
SYNC_COMMENT = "<!-- synced from Glawster/organiseMyProjects -- do not edit directly -->\n"

TARGET_REPOS = [
    "Glawster/organiseMyPhotos",
    "Glawster/linuxMigration",
    "Glawster/organiseMyVideo",
    "Glawster/createDirPerFile",
    "Glawster/b2-backup-scripts",
    "Glawster/sidecarEditor",
    "Glawster/myDavinciScripts",
    "Glawster/directPayments",
    "Glawster/imageRecognition",
    "Glawster/comfyuiWorkflows",
    "Glawster/batchImageProcessing",
    "Glawster/AbilityUsageTracker",
    "Glawster/OutdatedItemCleaner",
    "Glawster/wheresItAt"
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


def getRemoteFile(repo: str, path: str, headers: dict) -> Optional[dict]:
    """
    Fetch file metadata and content from the GitHub Contents API.

    Returns the parsed JSON response dict, or None if the file does not exist.
    Raises requests.HTTPError for unexpected API errors.
    """
    url = f"{API_BASE}/repos/{repo}/contents/{path}"
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def putRemoteFile(
    repo: str,
    path: str,
    content: str,
    sha: Optional[str],
    commitMessage: str,
    headers: dict,
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
) -> str:
    """
    Sync the copilot-instructions file to a single repo.

    Returns one of: "updated", "skipped", "failed".
    """
    prefix = "[] " if dryRun else ""

    logger.info(f"...checking {repo}")
    print(f"{prefix}checking {repo}...")

    try:
        remoteData = getRemoteFile(repo, TARGET_PATH, headers)

        if remoteData is not None:
            # Decode existing content
            remoteContent = base64.b64decode(remoteData["content"]).decode("utf-8")
            sha = remoteData["sha"]

            if remoteContent == targetContent:
                logger.info("...already up to date, skipping")
                print(f"{prefix}already up to date, skipping")
                return "skipped"

            if verbose:
                logger.info("...content differs, updating")
        else:
            sha = None
            if verbose:
                logger.info("...file does not exist, creating")

        if dryRun:
            logger.info(f"...would update {TARGET_PATH} (content differs)")
            print(f"{prefix}would update {TARGET_PATH} (content differs)")
            return "updated"

        putRemoteFile(repo, TARGET_PATH, targetContent, sha, COMMIT_MESSAGE, headers)
        logger.info(f"...updated {TARGET_PATH}")
        print(f"updated {TARGET_PATH}")
        return "updated"

    except requests.HTTPError as exc:
        logger.error(f"Failed to sync {repo}: {exc}")
        print(f"ERROR: failed to sync {repo}: {exc}", file=sys.stderr)
        return "failed"
    except requests.RequestException as exc:
        logger.error(f"Network error syncing {repo}: {exc}")
        print(f"ERROR: network error syncing {repo}: {exc}", file=sys.stderr)
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
    prefix = "[] " if dryRun else ""

    _name = Path(__file__).stem
    logger = getLogger(_name, includeConsole=False)

    # Resolve the GitHub token
    token = args.token or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("ERROR: no GitHub token found. Set GITHUB_TOKEN or use --token.", file=sys.stderr)
        sys.exit(1)

    # Read the source file
    if not SOURCE_FILE.exists():
        print(f"ERROR: source file not found: {SOURCE_FILE}", file=sys.stderr)
        sys.exit(1)

    sourceContent = SOURCE_FILE.read_text(encoding="utf-8")
    targetContent = buildTargetContent(sourceContent)

    headers = buildHeaders(token)

    if dryRun:
        print("DRY-RUN MODE: no changes will be made (use --confirm to execute)")

    counts = {"updated": 0, "skipped": 0, "failed": 0}

    for repo in TARGET_REPOS:
        result = syncRepo(repo, targetContent, dryRun, headers, logger, args.verbose)
        counts[result] += 1

    dryRunNote = " (dry-run)" if dryRun else ""
    print(
        f"\nSummary: {counts['updated']} updated, "
        f"{counts['skipped']} skipped, "
        f"{counts['failed']} failed{dryRunNote}"
    )


if __name__ == "__main__":
    main()
