# Developer Documentation

This document provides detailed information for developers working on the
`organiseMyProjects` package.

## Architecture Overview

The `organiseMyProjects` package consists of several key components:

### Core Modules

#### `manageProject.py`

The main module responsible for project scaffolding functionality.

**Key Functions:**

Create
  Creates a new project.
  May create application scaffold, dependencies and requested UI/Qt scaffold.

Update
  Refreshes OMP-owned managed files.
  Never creates or modifies project-owned application scaffold.

Migrate
  Adds missing modern OMP project-management/context structures.
  Never overwrites existing project-owned content.
  Never creates generic application/UI scaffold.

Check
  Read-only validation of repository and agent readiness.

**Changes from previous behaviour:**

.env
  OMP no longer creates one merely to manipulate PYTHONPATH.

requirements.txt
  No universal pywin32 dependency.

UI / Qt
  Creation-time scaffold options.
  Not update behaviour.

DOC-001
  Root README is not the authoritative index of project/agent knowledge.

**Templates and Constants:**

- `GITIGNORE_CONTENT` - Standard .gitignore content for Python projects
- `REQUIREMENTS_CONTENT` - Base production dependencies
- `DEV_REQUIREMENTS_CONTENT` - Development dependencies
- `ENV_CONTENT` - Environment configuration template
- `MAIN_PY_CONTENT` - Main application entry point template
- `PRECOMMIT_CONTENT` - Pre-commit configuration template

`updateProject()` no longer creates dated backup copies. Users should review the
resulting Git/VS Code changed files and revert any scaffold-managed updates they
do not want before committing.

OMP 0.5 performs two narrowly scoped filename migrations. A legacy
`test_Foo.py` becomes `test_foo.py` only when the destination is absent. A
legacy single-prompt name such as `007-feature.prompt.md` becomes
`007-feature.md` only when `features/007-feature.md` proves the relationship and
the destination is absent; the requirements index link is updated with it.
Ambiguous or colliding names are reported and left unchanged.

#### `logUtils.py`

Centralised logging utilities shared across organiseMyProjects tooling.

**Key Functions:**

- `thisApplication` - Name of the application
- `setupLogging(thisApplication, logDir, level, includeConsole)` -
    Create/retrieve a named logger with a `FileHandler`
- `getLogger(thisApplication, logDir, level, includeConsole)` - Convenience
    wrapper around `setupLogging`
- `setLogLevel(level, targetLogger)` - Change the log level of a logger at
    runtime
- `cleanOldLogFiles(logDir, daysToKeep)` - Remove log files older than the
    specified number of days
- `drawBox(message, border_char, corner_char, side_char, padding, logger)` -
    Print or log a text message surrounded by a Unicode box

**Dry-run progress logging:**

`getLogger(..., dryRun=True)` marks the full progress sequence while preserving
the ellipsis convention: `[] doing...`, `...[] action`, and `...[] done`.
The `doing`, `action`, and `done` methods each accept an optional
`dryRunMessage`; it replaces the normal message only during a dry-run. Calls
that omit it remain valid. Informational methods (`info`, `value`, and
`multiline`) are not marked because they report facts observed by the run.

The shell equivalents accept the optional dry-run message as their second
argument: `log_doing`, `log_action`, and `log_done`.

**`drawBox` Details:**

Draws an ASCII/Unicode box around a (potentially multi-line) message to make
it visually prominent in logs or console output.

```text
+--------------------------------------------------------+
|  [ERROR] Database connection failed                    |
|  Attempted 3 retries. Check credentials and network.   |
+--------------------------------------------------------+
```

Parameter details:

- `message` (`str`, required): Text to display; may contain `\n` for multiple
    lines.
- `border_char` (`str`, default `"-"`): Character used for horizontal border
    lines.
- `corner_char` (`str`, default `"+"`): Character used at the four corners.
- `side_char` (`str`, default `"|"`): Character used for vertical side
    borders.
- `padding` (`int`, default `2`): Spaces between text and the side borders.
- `logger` (`logging.Logger` or `None`, default `None`): If provided, each line
    is emitted via `logger.info()`; otherwise output goes to `print()`.

**Usage Examples:**

```python
from organiseMyProjects.logUtils import drawBox, getLogger, thisApplication

# Print to stdout
drawBox("Deployment complete")

# Log via a logger instance
log = getLogger(thisApplication)
drawBox("[ERROR] Database connection failed\nAttempted 3 retries.", logger=log)

# Custom box characters
drawBox("Warning", border_char="-", corner_char="*", side_char="|")
```

#### `guiNamingLinter.py`

Implements custom linting rules for GUI naming conventions and code formatting.

**Key Classes:**

- `GuiNamingVisitor(ast.NodeVisitor)` - AST visitor for analyzing Python code

**Key Functions:**

- `lintFile(filename)` - Lint a single Python file
- `lintGuiNaming(directory)` - Recursively lint a directory

**Naming Rules:**

```python
namingRules = {
    'Button': r'^btn[A-Z]\w+',
    'Entry': r'^entry[A-Z]\w+',
    'Label': r'^lbl[A-Z]\w+',
    'Frame': r'^frm[A-Z]\w+',
    'Text': r'^txt[A-Z]\w+',
    'Listbox': r'^lst[A-Z]\w+',
    'Checkbutton': r'^chk[A-Z]\w+',
    'Radiobutton': r'^rdo[A-Z]\w+',
    'Combobox': r'^cmb[A-Z]\w+',
    'Handler': r'^on[A-Z]\w+',
    'Constant': r'^[A-Z_]+$',
    'Class': r'^[A-Z][a-zA-Z0-9]*$',
}
```

#### `runLinter.py`

Command-line interface for the GUI naming linter.

**Key Functions:**

- `main()` - Entry point for command-line usage
- `_lint_target(target)` - Lint a specific file or directory

**Markup Linting Flags:**

- `--markup` - Run markdown checks in check-only mode
- `--markup --fix` - Run markdown checks and apply automatic fixes

Legacy compatibility: `--fix-markup` is still supported.

The markup flow calls `markdownlint-cli@0.31.1` through `npx`, disables
MD013 (line-length), and ignores `build` and `.pytest_cache` by default.

#### `fixMarkup.py`

Markup lint helper used by the CLI and available as a standalone command.

**Key Functions:**

- `markupFix(targets=None, fix=True)` - Run markup lint with optional fixing
- `main()` - CLI entry point (`fixMarkup`)

## Package Resources

The package includes template files that are distributed with the package:

- `.github/agent-instructions.md` - Master AI coding agent development
    guidelines
- `.github/copilot-instructions.md` - Identical GitHub Copilot compatibility
    copy
- `.github/repositoryLayout.md` - Canonical project layout definition copied to
    generated repositories
- `.github/requirementsManagement.md` - Canonical requirements workflow copied
    to generated repositories
- `documentation/testingProcess.md` - Canonical testing process copied to
    generated repositories
- Template Python modules (copied to new projects)

## Canonical Agent Instructions Access

The canonical Agent instructions live in the repository root `.github/`
directory and are copied into generated projects from there:

```python
try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    from importlib_resources import files

# Access repository root files
repo_root = files('organiseMyProjects').parent
agent_file = repo_root / '.github' / 'agent-instructions.md'
content = agent_file.read_text()
```

## Testing Framework

### Test Structure

The test suite is organized into several modules:

#### `tests/conftest.py`

Shared test fixtures and configuration:

- `temp_dir` - Temporary directory fixture
- `sample_project_name` - Standard test project name
- `mockPythonFile` - Sample Python file with violations

#### `tests/test_logUtils.py`

Tests for logging utilities:

- `TestDrawBox` - Box-drawing function tests

#### `tests/test_createProject.py`

Tests for project creation functionality:

- `TestCreateProject` - Basic project creation tests
- `TestUpdateProject` - Project update functionality tests
- `TestUtilityFunctions` - Utility function tests

#### `tests/test_guiNamingLinter.py`

Tests for linting functionality:

- `TestGuiNamingVisitor` - AST visitor tests
- `TestLintFile` - File linting tests
- `TestLintGuiNaming` - Directory linting tests
- `TestNamingPatterns` - Naming pattern validation tests

#### `tests/test_runLinter.py`

Tests for command-line interface:

- `TestRunLinter` - CLI functionality tests
- `TestIntegration` - Complete workflow tests

#### `tests/test_integration.py`

End-to-end integration tests:

- `TestPackageInstallation` - Entry point tests
- `TestEndToEndWorkflow` - Complete workflow tests
- `TestErrorHandling` - Error scenario tests
- `TestModuleImports` - Import verification tests
- `TestResourceAccess` - Package resource tests

#### `tests/test_syncAgentInstructions.py`

Tests for Agent instructions sync utility:

- `TestBuildTargetContent` - Content building tests
- `TestBuildHeaders` - HTTP header tests
- `TestGetRemoteFile` - Remote file retrieval tests
- `TestRepoSelect` - Interactive and named single-repository selection tests
- `TestSyncRepo` - Sync operation tests

### Running Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_createProject.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=organiseMyProjects

# Run specific test class
pytest tests/test_createProject.py::TestCreateProject

# Run specific test method
pytest tests/test_createProject.py::TestCreateProject::\
testCreateProjectBasicStructure
```

### Test Patterns

#### Using Fixtures

```python
def test_example(temp_dir, sample_project_name):
    """Test using shared fixtures."""
    project_path = temp_dir / sample_project_name
    # Test implementation
```

#### Mocking External Dependencies

```python
@patch('organiseMyProjects.manageProject.subprocess.run')
def test_with_mocked_subprocess(mock_subprocess):
    """Test with mocked subprocess calls."""
    createProject("test_project")
    mock_subprocess.assert_called()
```

#### Testing File Operations

```python
def test_file_creation(temp_dir):
    """Test file creation in temporary directory."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
    assert test_file.read_text() == "content"
```

## Development Workflow

### Setting Up Development Environment

1. Clone the repository
2. Install development dependencies:

   ```bash
   pip install pytest black ruff
   ```

3. Install the package in development mode:

   ```bash
   pip install -e .
   ```

### Code Quality Standards

#### Formatting

- Use `black` for code formatting
- Use `ruff check .` for static analysis
- Line length: 88 characters (black default)
- Use double quotes for strings

#### Naming Conventions

- Functions and variables: `camelCase`
- Classes: `PascalCase`
- Constants: `UPPER_CASE_WITH_UNDERSCORES`
- Private members: `_leadingUnderscore`

#### Documentation

- Use docstrings for all public functions and classes
- Follow Google docstring format
- Include type hints where appropriate

#### Testing

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Test both success and failure scenarios

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black

  - repo: local
    hooks:
      - id: gui-naming-linter
        name: GUI Naming Linter
        entry: python -m organiseMyProjects.runLinter
        language: python
        additional_dependencies:
          - -e .
        types: [python]
```

### Release Process

1. Update `VERSION` in `organiseMyProjects/version.py`
2. Update `CHANGELOG.md` (if exists)
3. Run full test suite: `pytest`
4. Run linter: `runLinter .`
5. Format code: `black .`
6. Run static checks: `ruff check .`
7. Build package: `python setup.py sdist`
8. Test installation: `pip install dist/organiseMyProjects-*.tar.gz`
9. Tag the commit with the same release value as `VERSION`

## Extending the Package

### Adding New Linting Rules

To add new linting rules to `guiNamingLinter.py`:

1. Add the rule to `namingRules` dictionary
2. Update the `GuiNamingVisitor` class to check for the new rule
3. Add tests for the new rule in `tests/test_guiNamingLinter.py`

Example:

```python
# In namingRules
'NewWidget': r'^new[A-Z]\w+',

# In GuiNamingVisitor
def visit_Assign(self, node):
    # Add logic to check for NewWidget pattern
    pass
```

### Adding New Template Files

To add new template files to projects:

1. Create the template file in the package directory
2. Add it to `MANIFEST.in` if needed
3. Update `createProject()` to copy the file
4. Update `updateProject()` to handle updates
5. Add tests for the new template

### Adding New Command-Line Tools

To add new entry points:

Only executable applications and command-line tools need an entry point. A
reusable library module or package does not require `main.py`.

1. Create the module with a `main()` function
2. Add entry point to `setup.py`:

   ```python
   entry_points={
       "console_scripts": [
           "newTool=organiseMyProjects.newTool:main",
       ]
   }
   ```

3. Add tests for the new tool

## Troubleshooting

### Common Issues

#### Import Errors

- Ensure the package is installed: `pip install -e .`
- Check Python path includes the package directory
- Verify all `__init__.py` files exist

#### Resource Access Issues

- Ensure files are included in `MANIFEST.in`
- Check that `include_package_data=True` in `setup.py`
- Verify resource access uses `importlib.resources`

#### Test Failures

- Run tests with `-v` flag for verbose output
- Check that fixtures are properly imported
- Ensure test isolation (use `temp_dir` fixture)

### Debugging Tips

#### Debugging Project Creation

```python
# Add debug prints to manageProject.py
print(f"Creating project at: {basePath}")
print(f"Template dir: {TEMPLATE_DIR}")
```

#### Debugging Linting Issues

```python
# Add debug prints to guiNamingLinter.py
print(f"Checking node: {ast.dump(node)}")
print(f"Current violations: {self.violations}")
```

#### Debugging Resource Access

```python
# Check package resource availability
from importlib.resources import files
package_files = files('organiseMyProjects')
print(list(package_files.iterdir()))
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Run code quality checks
6. Submit pull request with description

### Code Review Guidelines

- Ensure new functionality includes tests
- Verify documentation is updated
- Check code follows project conventions
- Test on different Python versions if possible

### Issue Reporting

When reporting issues:

- Include Python version and OS
- Provide minimal reproduction case
- Include full error traceback
- Describe expected vs actual behavior
