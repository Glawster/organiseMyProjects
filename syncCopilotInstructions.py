#!/usr/bin/env python3
"""
syncCopilotInstructions.py

Syncs canonical instruction files from organiseMyProjects
out to all other Glawster repos that use the shared template.

Default mode is dry-run; use --confirm to actually push changes.
Use --merge to merge conflict-free sync branches into each default branch.

This script always writes to a generated destination branch named:
sync/instructions-YYYYMMDD
"""

import argparse
import base64
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Optional

import requests

from organiseMyProjects.logUtils import getLogger, thisApplication

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SYNC_SPECS = [
    {
        "sourceFile": Path(__file__).resolve().parent / ".github" / "copilot-instructions.md",
        "targetPath": ".github/copilot-instructions.md",
        "commitMessage": "sync: update copilot-instructions.md from organiseMyProjects template",
    },
    {
        "sourceFile": Path(__file__).resolve().parent / "AGENTS.md",
        "targetPath": "AGENTS.md",
        "commitMessage": "sync: update AGENTS.md from organiseMyProjects template",
    },
]
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
    "Glawster/myHandbook",
]

API_BASE = "https://api.github.com"
CONFIG_PATH = (
    Path.home()
    / ".config"
    / "organiseMyProjects"
    / "syncCopilotInstructions.json"
)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


def configLoadToken(configPath: Path = CONFIG_PATH) -> str:
    """Return the stored GitHub token, or an empty string if unavailable."""
    try:
        data = json.loads(configPath.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return ""

    token = data.get("githubToken", "") if isinstance(data, dict) else ""
    return token if isinstance(token, str) else ""


def configSaveToken(token: str, configPath: Path = CONFIG_PATH) -> None:
    """Store the GitHub token in the user config directory with private access."""
    configPath.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    configPath.write_text(
        json.dumps({"githubToken": token}, indent=2) + "\n",
        encoding="utf-8",
    )
    configPath.chmod(0o600)


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


def mergeBranch(repo: str, branch: str, base: str, headers: dict) -> str:
    """Merge branch into base when GitHub can do so without conflicts.

    Returns one of: "merged", "already_merged", "conflict", "failed". A
    conflicting merge leaves the generated branch available for manual review.
    """
    url = f"{API_BASE}/repos/{repo}/merges"
    payload = {
        "base": base,
        "head": branch,
        "commit_message": f"Merge {branch} into {base}",
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 204:
            return "already_merged"
        if response.status_code == 409:
            return "conflict"
        response.raise_for_status()
        return "merged"
    except requests.HTTPError:
        return "failed"
    except requests.RequestException:
        return "failed"


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def buildTargetContent(sourceContent: str) -> str:
    """Return the content to write to each target repo (with sync comment prepended)."""
    return SYNC_COMMENT + sourceContent


def syncRepo(
    repo: str,
    targetPath: str,
    targetContent: str,
    commitMessage: str,
    dryRun: bool,
    headers: dict,
    logger,
    verbose: bool,
    branch: Optional[str] = None,
) -> str:
    """
    Sync one instruction file to a single repo.

    Returns one of: "updated", "ready", "skipped", "failed". "ready" means
    the target content already exists on the generated sync branch.
    """
    logger.doing("checking repository")
    logger.value("repository", repo)

    try:
        # Try sync branch first if it exists (reuse branch from same day)
        remoteData = None
        foundOnBranch = False
        if branch:
            logger.value("branch", branch)
            remoteData = getRemoteFile(repo, targetPath, headers, ref=branch)
            foundOnBranch = remoteData is not None
            if remoteData is not None and verbose:
                logger.info("using existing branch")

        # If branch doesn't have the file, check default branch
        if remoteData is None:
            remoteData = getRemoteFile(repo, targetPath, headers, ref=None)

        if remoteData is not None:
            # Decode existing content
            remoteContent = base64.b64decode(remoteData["content"]).decode("utf-8")
            sha = remoteData["sha"]

            if remoteContent == targetContent:
                if foundOnBranch:
                    logger.info("sync branch already up to date, ready to merge")
                    return "ready"
                logger.info("default branch already up to date, skipping")
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

        logger.value("target path", targetPath)
        logger.action("update target file")
        if dryRun:
            return "updated"

        putRemoteFile(
            repo,
            targetPath,
            targetContent,
            sha,
            commitMessage,
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
        description="Sync instruction files to all Glawster target repos."
    )
    parser.add_argument(
        "-y",
        "--confirm",
        action="store_true",
        help="execute the sync (default is dry-run)",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="merge conflict-free sync branches into each default branch",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="GitHub PAT (overrides GITHUB_TOKEN and is saved in ~/.config)",
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

    syncBranch = f"sync/instructions-{datetime.date.today().strftime('%Y%m%d')}"
    logger.value("sync branch", syncBranch)

    # Resolve the GitHub token. Explicit and environment tokens refresh the store.
    suppliedToken = args.token or os.environ.get("GITHUB_TOKEN", "")
    token = suppliedToken or configLoadToken()
    if not token:
        logger.error(
            "No GitHub token found. Set GITHUB_TOKEN, use --token, or add it to %s.",
            CONFIG_PATH,
        )
        sys.exit(1)
    if suppliedToken:
        try:
            configSaveToken(suppliedToken)
            logger.info("GitHub token saved to user config")
        except OSError as exc:
            logger.warning("Could not save GitHub token to %s: %s", CONFIG_PATH, exc)

    # Validate source files
    for spec in SYNC_SPECS:
        if not spec["sourceFile"].exists():
            logger.error("Source file not found: %s", spec["sourceFile"])
            sys.exit(1)

    logger.value("source file count", len(SYNC_SPECS))
    logger.value("target repo count", len(TARGET_REPOS))

    headers = buildHeaders(token)

    if dryRun:
        logger.info("dry-run mode: no changes will be made")

    counts = {"updated": 0, "ready": 0, "skipped": 0, "failed": 0}
    repoResults = {repo: [] for repo in TARGET_REPOS}

    for spec in SYNC_SPECS:
        logger.value("source file", spec["sourceFile"])
        sourceContent = spec["sourceFile"].read_text(encoding="utf-8")
        targetContent = buildTargetContent(sourceContent)

        for repo in TARGET_REPOS:
            result = syncRepo(
                repo,
                spec["targetPath"],
                targetContent,
                spec["commitMessage"],
                dryRun,
                headers,
                logger,
                args.verbose,
                branch=syncBranch,
            )
            counts[result] += 1
            repoResults[repo].append(result)

    mergeCounts = {
        "merged": 0,
        "already_merged": 0,
        "conflict": 0,
        "failed": 0,
    }
    manualReviewRepos = []
    if args.merge:
        for repo, results in repoResults.items():
            hasMergeableBranch = "updated" in results or "ready" in results
            if not hasMergeableBranch or "failed" in results:
                continue

            defaultBranch = getDefaultBranch(repo, headers)
            logger.action("merge sync branch")
            logger.value("repository", repo)
            logger.value("base branch", defaultBranch)
            if dryRun:
                mergeResult = "merged"
            else:
                mergeResult = mergeBranch(
                    repo, syncBranch, defaultBranch, headers
                )
            mergeCounts[mergeResult] += 1
            if mergeResult == "merged":
                logger.done("merge sync branch")
            elif mergeResult == "already_merged":
                logger.info("merge skipped: branch is already merged")
            elif mergeResult == "conflict":
                manualReviewRepos.append(repo)
                logger.warning(
                    "manual merge required for %s: %s cannot be merged into %s "
                    "without conflicts",
                    repo,
                    syncBranch,
                    defaultBranch,
                )
            else:
                logger.error(f"Failed to merge {syncBranch} in {repo}")

    logger.info(
        "summary updated=%s ready=%s skipped=%s failed=%s",
        counts["updated"],
        counts["ready"],
        counts["skipped"],
        counts["failed"],
    )
    if args.merge:
        logger.info(
            "merge summary merged=%s already_merged=%s conflicts=%s failed=%s",
            mergeCounts["merged"],
            mergeCounts["already_merged"],
            mergeCounts["conflict"],
            mergeCounts["failed"],
        )
        if manualReviewRepos:
            logger.warning(
                "manual review required for %s repositories: %s",
                len(manualReviewRepos),
                ", ".join(manualReviewRepos),
            )
    logger.done("finished")


if __name__ == "__main__":
    main()
