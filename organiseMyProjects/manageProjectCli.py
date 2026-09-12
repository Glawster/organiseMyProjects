"""Console entry point for manageProject.

Command routing lives with the project-management implementation so
``manageProject create|update|check|migrate|sync`` share one parser.
"""

import sys

from organiseMyProjects import manageProject


def main() -> int:
    """Dispatch manageProject commands."""
    result = manageProject.main()
    return 0 if result is None else result


if __name__ == "__main__":
    sys.exit(main())
