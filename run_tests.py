#!/usr/bin/env python
"""
Test runner script for organiseMyProjects.

This script provides a convenient way to run tests with various options.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(args):
    """Run pytest with the specified arguments."""
    cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=organiseMyProjects", "--cov-report=html", "--cov-report=term"])
    
    if args.file:
        cmd.append(args.file)
    else:
        cmd.append("tests/")
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    
    if args.collect_only:
        cmd.append("--collect-only")
    
    if args.failed_first:
        cmd.append("--failed-first")
    
    if args.exit_on_first:
        cmd.append("-x")
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Test runner for organiseMyProjects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py -v                 # Run with verbose output
  python run_tests.py --coverage         # Run with coverage report
  python run_tests.py -f test_createProject.py  # Run specific file
  python run_tests.py -k test_create     # Run tests matching keyword
  python run_tests.py --collect-only     # Show what tests would run
        """
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Run tests with verbose output"
    )
    
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Run tests with coverage report"
    )
    
    parser.add_argument(
        "-f", "--file", 
        help="Run tests from specific file"
    )
    
    parser.add_argument(
        "-m", "--markers", 
        help="Run tests with specific markers"
    )
    
    parser.add_argument(
        "-k", "--keyword", 
        help="Run tests matching keyword expression"
    )
    
    parser.add_argument(
        "--collect-only", 
        action="store_true",
        help="Only collect tests, don't run them"
    )
    
    parser.add_argument(
        "--failed-first", 
        action="store_true",
        help="Run failed tests first"
    )
    
    parser.add_argument(
        "-x", "--exit-on-first", 
        action="store_true",
        help="Exit on first test failure"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    if script_dir.name != "organiseMyProjects":
        print("Error: This script should be run from the organiseMyProjects directory")
        return 1
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("Error: pytest is not installed. Run: pip install pytest")
        return 1
    
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())