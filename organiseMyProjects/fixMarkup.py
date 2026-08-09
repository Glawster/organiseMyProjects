#!/usr/bin/env python3
"""Run markdown lint checks and optionally apply automatic fixes."""

from __future__ import annotations

import argparse
import subprocess


def _buildMarkupCommand(targets: list[str], fix: bool) -> list[str]:
    """Build the markdownlint-cli command for this project."""
    command = [
        "npx",
        "--yes",
        "markdownlint-cli@0.31.1",
        *targets,
        "--ignore",
        "build",
        "--ignore",
        ".pytest_cache",
    ]

    # Apply edits in-place only when explicitly requested.
    if fix:
        command.append("--fix")

    return command


def markupFix(targets: list[str] | None = None, fix: bool = True) -> int:
    """Run markdown linting and optionally apply fixes.

    Returns the markdownlint process exit code.
    """
    lintTargets = targets or ["**/*.md"]
    command = _buildMarkupCommand(lintTargets, fix=fix)

    modeLabel = "fix mode" if fix else "check mode"
    print(f"Running markup lint ({modeLabel})...")

    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError:
        print("Markup lint failed: npx is not installed or not on PATH.")
        return 2

    if result.returncode == 0:
        print("Markup lint completed with no remaining issues.")
    else:
        print("Markup lint reported issues.")
        if fix:
            # markdownlint only auto-fixes certain rule types.
            print(
                "Some rules are not auto-fixable (for example line-length), "
                "so manual edits or rule configuration may still be needed."
            )

    return result.returncode


def main() -> None:
    """CLI entry point for markup linting/fixing."""
    parser = argparse.ArgumentParser(
        description="Run markdown lint checks and optionally apply fixes"
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Markdown files or glob patterns to lint; defaults to **/*.md",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check markdown files; do not apply automatic fixes",
    )
    args = parser.parse_args()

    fixMode = not args.check
    exitCode = markupFix(targets=args.targets or None, fix=fixMode)
    raise SystemExit(exitCode)


if __name__ == "__main__":
    main()