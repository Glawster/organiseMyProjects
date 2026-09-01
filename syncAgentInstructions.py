#!/usr/bin/env python3
"""
syncAgentInstructions.py

Syncs canonical instruction files from organiseMyProjects
out to all other Glawster repos that use the shared template.

Default mode is dry-run; use --confirm to actually push changes.
Use --merge to create and merge conflict-free pull requests into each default branch.

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

from organiseMyProjects.logUtils import getLogger, setApplication
from organiseMyProjects.managedContent import (
    managedContentBuild,
)
from organiseMyProjects.version import VERSION

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SYNC_SPECS = [
    {
        "sourceFile": Path(__file__).resolve().parent
        / ".github"
        / "agent-instructions.md",
        "targetPath": ".github/agent-instructions.md",
        "commitMessage": "sync: update agent-instructions.md from organiseMyProjects template",
    },
    {
        "sourceFile": Path(__file__).resolve().parent
        / ".github"
        / "copilot-instructions.md",
        "targetPath": ".github/copilot-instructions.md",
        "commitMessage": "sync: update Copilot compatibility instructions",
    },
    {
        "sourceFile": Path(__file__).resolve().parent / ".github" / "CLAUDE.md",
        "targetPath": "CLAUDE.md",
        "commitMessage": "sync: update Claude Code instructions pointer",
    },
    {
        "sourceFile": Path(__file__).resolve().parent / ".github" / "AGENTS.md",
        "targetPath": "AGENTS.md",
        "commitMessage": "sync: update AGENTS.md from organiseMyProjects template",
    },
    {
        "sourceFile": Path(__file__).resolve().parent
        / "documentation"
        / "repositoryLayout.md",
        "targetPath": "documentation/repositoryLayout.md",
        "commitMessage": "sync: update repository layout definition",
    },
    {
        "sourceFile": Path(__file__).resolve().parent
        / "documentation"
        / "requirementsManagement.md",
        "targetPath": "documentation/requirementsManagement.md",
        "commitMessage": "sync: update requirements management guide",
    },
    {
        "sourceFile": Path(__file__).resolve().parent
        / "documentation"
        / "howToRelease.md",
        "targetPath": "documentation/howToRelease.md",
        "commitMessage": "sync: update release process guide",
    },
    {
        "sourceFile": Path(__file__).resolve().parent
        / "documentation"
        / "testingProcess.md",
        "targetPath": "documentation/testingProcess.md",
        "commitMessage": "sync: update testing process guide",
    },
]
API_BASE = "https://api.github.com"
REPO_OWNER = "Glawster"
SOURCE_REPO = f"{REPO_OWNER}/organiseMyProjects"
CONFIG_PATH = (
    Path.home() / ".config" / "organiseMyProjects" / "syncAgentInstructions.json"
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


def getTargetRepos(headers: dict) -> list[str]:
    """Return active, owned, non-fork repositories eligible for syncing."""
    url = f"{API_BASE}/user/repos"
    page = 1
    repos = []

    while True:
        params = {
            "affiliation": "owner",
            "per_page": 100,
            "page": page,
        }
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        pageRepos = response.json()
        repos.extend(pageRepos)
        if len(pageRepos) < 100:
            break
        page += 1

    targets = [
        repo["full_name"]
        for repo in repos
        if repo.get("owner", {}).get("login", "").casefold() == REPO_OWNER.casefold()
        and repo.get("full_name") != SOURCE_REPO
        and not repo.get("archived", False)
        and not repo.get("fork", False)
    ]
    return sorted(targets, key=str.casefold)


def repoSelect(targetRepos: list[str], requestedRepo: Optional[str]) -> list[str]:
    """Return all repositories or the single repository requested by the user."""
    if requestedRepo is None:
        return targetRepos
    if not targetRepos:
        raise ValueError("No eligible repositories were found")

    if requestedRepo:
        requestedName = requestedRepo.casefold()
        matches = [
            repo
            for repo in targetRepos
            if repo.casefold() == requestedName
            or repo.rpartition("/")[2].casefold() == requestedName
        ]
        if len(matches) == 1:
            return matches
        if len(matches) > 1:
            raise ValueError(
                f"Repository name is ambiguous; use owner/name: {requestedRepo}"
            )
        raise ValueError(
            f"Repository is not eligible or was not found: {requestedRepo}"
        )

    print("Eligible repositories:")
    for index, repo in enumerate(targetRepos, start=1):
        print(f"  {index}. {repo}")

    while True:
        try:
            response = input("Select a repository number: ").strip()
        except (EOFError, KeyboardInterrupt) as exc:
            raise ValueError("Repository selection cancelled") from exc

        if response.isdigit():
            selectedIndex = int(response)
            if 1 <= selectedIndex <= len(targetRepos):
                return [targetRepos[selectedIndex - 1]]
        print(f"Enter a number from 1 to {len(targetRepos)}.")


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


def createPullRequest(repo: str, branch: str, base: str, headers: dict) -> dict:
    """Create a pull request for the generated sync branch."""
    url = f"{API_BASE}/repos/{repo}/pulls"
    payload = {
        "title": "Sync shared agent instructions",
        "body": (
            "Automated sync from `Glawster/organiseMyProjects`.\n\n"
            "This pull request was created by `syncAgentInstructions.py`."
        ),
        "head": branch,
        "base": base,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def getPullRequest(repo: str, branch: str, base: str, headers: dict) -> Optional[dict]:
    """Return the newest PR for branch and base, including closed PRs."""
    owner = repo.split("/", maxsplit=1)[0]
    url = f"{API_BASE}/repos/{repo}/pulls"
    params = {
        "state": "all",
        "head": f"{owner}:{branch}",
        "base": base,
        "sort": "created",
        "direction": "desc",
    }
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    pullRequests = response.json()
    return pullRequests[0] if pullRequests else None


def mergePullRequest(repo: str, pullNumber: int, headers: dict) -> str:
    """Merge a pull request when GitHub considers it mergeable."""
    url = f"{API_BASE}/repos/{repo}/pulls/{pullNumber}/merge"
    payload = {"merge_method": "merge"}
    response = requests.put(url, json=payload, headers=headers, timeout=15)
    if response.status_code in (405, 409):
        return "conflict"
    response.raise_for_status()
    return "merged" if response.json().get("merged") else "conflict"


def syncPullRequest(
    repo: str, branch: str, base: str, headers: dict
) -> tuple[str, Optional[int]]:
    """Create or reuse the sync PR and merge it when possible.

    Returns a merge status and the pull request number, when one exists.
    """
    try:
        pullRequest = getPullRequest(repo, branch, base, headers)
        if pullRequest and pullRequest.get("merged_at"):
            return "already_merged", pullRequest["number"]
        if not pullRequest or pullRequest.get("state") != "open":
            pullRequest = createPullRequest(repo, branch, base, headers)

        pullNumber = pullRequest["number"]
        return mergePullRequest(repo, pullNumber, headers), pullNumber
    except requests.HTTPError:
        return "failed", None
    except requests.RequestException:
        return "failed", None


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def buildTargetContent(sourceContent: str, targetPath: str = "") -> str:
    """Return the content to write to each target repo (with sync comment prepended)."""
    suffix = Path(targetPath).suffix if targetPath else ".md"
    if suffix == "":
        suffix = ".md"
    return managedContentBuild(sourceContent, suffix=suffix, sync=True)


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
    preparedBranches: Optional[set[str]] = None,
) -> str:
    """
    Sync one instruction file to a single repo.

    Returns one of: "updated", "ready", "skipped", "failed". "ready" means
    the target content already exists on the generated sync branch.
    """
    logger.info("checking repository")
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
                    logger.info("sync branch already up to date and ready to merge")
                    return "ready"
                logger.info("default branch already up to date, skipping")
                return "skipped"

            if verbose:
                logger.info("content differs, updating")
        else:
            sha = None
            if verbose:
                logger.info("file does not exist, creating")

        # Prepare one shared sync branch per repository, then reuse it for every file.
        if branch and (preparedBranches is None or repo not in preparedBranches):
            defaultBranch = getDefaultBranch(repo, headers)
            defaultSha = getBranchHeadSha(repo, defaultBranch, headers)
            logger.action("prepare sync branch")
            if not dryRun:
                createBranch(repo, branch, defaultSha, headers)
                logger.done("prepare sync branch")
            if preparedBranches is not None:
                preparedBranches.add(repo)

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
        help="create and merge conflict-free sync pull requests",
    )
    parser.add_argument(
        "--repo",
        nargs="?",
        const="",
        default=None,
        metavar="OWNER/REPO",
        help=("sync one repository; omit the value to choose from a numbered list"),
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

    thisApplication = "syncAgentInstructions"
    setApplication(thisApplication)
    logger = getLogger(includeConsole=True, dryRun=dryRun)
    logger.doing("starting")
    logger.value("OMP version", VERSION)
    logger.value("dryRun", dryRun)

    syncBranch = f"sync/instructions-{datetime.date.today().strftime('%Y%m%d')}"
    logger.value("sync branch", syncBranch)

    # Resolve the GitHub token. Explicit and environment tokens refresh the store.
    suppliedToken = args.token or os.environ.get("GITHUB_TOKEN", "")
    token = suppliedToken or configLoadToken()
    if not token:
        logger.error(
            f"No GitHub token found. Set GITHUB_TOKEN, use --token, or add it to {CONFIG_PATH}."
        )
        sys.exit(1)
    if suppliedToken:
        try:
            configSaveToken(suppliedToken)
            logger.info("github token saved to user config")
        except OSError as exc:
            logger.warning(f"could not save github token to {CONFIG_PATH}: {exc}")

    # Validate source files
    for spec in SYNC_SPECS:
        if not spec["sourceFile"].exists():
            logger.error(f"Source file not found: {spec['sourceFile']}")
            sys.exit(1)

    headers = buildHeaders(token)
    try:
        targetRepos = getTargetRepos(headers)
    except requests.RequestException as exc:
        logger.error(f"Could not list GitHub repositories: {exc}")
        sys.exit(1)

    try:
        targetRepos = repoSelect(targetRepos, args.repo)
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)

    logger.value("source file count", len(SYNC_SPECS))
    logger.value("target repo count", len(targetRepos))

    if dryRun:
        logger.info("dry-run mode: no changes will be made")

    counts = {"updated": 0, "ready": 0, "skipped": 0, "failed": 0}
    repoResults = {repo: [] for repo in targetRepos}
    preparedBranches: set[str] = set()

    sourcePayloads = []
    for spec in SYNC_SPECS:
        sourceContent = spec["sourceFile"].read_text(encoding="utf-8")
        sourcePayloads.append(
            {
                "sourceFile": spec["sourceFile"],
                "targetPath": spec["targetPath"],
                "commitMessage": spec["commitMessage"],
                "targetContent": buildTargetContent(sourceContent, spec["targetPath"]),
            }
        )

    for repo in targetRepos:
        logger.doing(f"syncing repository {repo}")
        for payload in sourcePayloads:
            result = syncRepo(
                repo,
                payload["targetPath"],
                payload["targetContent"],
                payload["commitMessage"],
                dryRun,
                headers,
                logger,
                args.verbose,
                branch=syncBranch,
                preparedBranches=preparedBranches,
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
            logger.action("create or reuse sync pull request")
            logger.value("repository", repo)
            logger.value("base branch", defaultBranch)
            if dryRun:
                mergeResult = "merged"
                pullNumber = None
            else:
                mergeResult, pullNumber = syncPullRequest(
                    repo, syncBranch, defaultBranch, headers
                )
            mergeCounts[mergeResult] += 1
            if pullNumber is not None:
                logger.value("pull request", f"#{pullNumber}")
            if mergeResult == "merged":
                logger.done("merge sync pull request")
            elif mergeResult == "already_merged":
                logger.info("merge skipped: pull request is already merged")
            elif mergeResult == "conflict":
                manualReviewRepos.append(repo)
                logger.warning(
                    f"manual review required for {repo} pull request #{pullNumber}: "
                    f"{syncBranch} cannot currently be merged into {defaultBranch}"
                )
            else:
                logger.error(f"Failed to create or merge a pull request in {repo}")

    logger.action(
        f"summary updated={counts['updated']} ready={counts['ready']} "
        f"skipped={counts['skipped']} failed={counts['failed']}"
    )
    if args.merge:
        logger.action(
            f"merge summary merged={mergeCounts['merged']} "
            f"already_merged={mergeCounts['already_merged']} "
            f"conflicts={mergeCounts['conflict']} failed={mergeCounts['failed']}"
        )
        if manualReviewRepos:
            logger.warning(
                f"manual review required for {len(manualReviewRepos)} repositories: "
                f"{', '.join(manualReviewRepos)}"
            )
    logger.done("finished")


if __name__ == "__main__":
    main()
