"""Console entry point for manageProject.

Keeps command routing separate from the project-management implementation so
agent-readiness validation can remain a reusable module while being exposed as
``manageProject --check``.
"""

import argparse
import sys
from pathlib import Path

from organiseMyProjects import manageProject
from organiseMyProjects.agentCheck import checkProject


def _checkParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manageProject",
        description="Validate project agent-readiness and context integrity.",
    )
    parser.add_argument("--check", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "project",
        nargs="?",
        default=None,
        help="Project directory to validate (default: current directory)",
    )
    parser.add_argument(
        "-p",
        "--project",
        dest="projectOption",
        default=None,
        help="Legacy named project path; prefer the positional project argument",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed validation output",
    )
    return parser


def _checkMain(argv: list[str]) -> int:
    parser = _checkParser()
    args = parser.parse_args(argv)

    if args.project is not None and args.projectOption is not None:
        parser.error(
            "Use either the positional project argument or the --project flag, not both."
        )

    projectPath = args.project if args.project is not None else args.projectOption
    targetPath = Path(projectPath) if projectPath is not None else Path.cwd()
    return checkProject(targetPath, strict=args.strict, verbose=args.verbose)


def main() -> int:
    """Dispatch manageProject commands, including the read-only --check mode."""
    argv = sys.argv[1:]
    if "--check" in argv:
        incompatible = {
            "--create",
            "--update",
            "-u",
            "--sync",
            "--confirm",
            "-y",
            "--ui",
            "-qt",
            "--qt",
            "--add-scaffold",
            "--merge",
            "--repo",
            "--token",
        }
        conflict = next((arg for arg in argv if arg in incompatible), None)
        if conflict is not None:
            parser = _checkParser()
            parser.error(f"--check cannot be combined with {conflict}.")
        return _checkMain(argv)

    result = manageProject.main()
    return 0 if result is None else result


if __name__ == "__main__":
    sys.exit(main())
