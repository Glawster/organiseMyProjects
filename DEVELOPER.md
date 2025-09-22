# Developer Documentation

This document provides detailed information for developers working on the `organiseMyProjects` package.

## Architecture Overview

The `organiseMyProjects` package consists of several key components:

### Core Modules

#### `createProject.py`
The main module responsible for project scaffolding functionality.

**Key Functions:**
- `createProject(projectName)` - Creates a new project with complete structure
- `updateProject(projectName)` - Updates existing project with latest templates
- `_copy_if_newer(src, dest)` - Utility for conditional file copying
- `_update_text_file(dest, content)` - Utility for updating text files with binary comparison

**Templates and Constants:**
- `GITIGNORE_CONTENT` - Standard .gitignore content for Python projects
- `REQUIREMENTS_CONTENT` - Base production dependencies
- `DEV_REQUIREMENTS_CONTENT` - Development dependencies
- `ENV_CONTENT` - Environment configuration template
- `MAIN_PY_CONTENT` - Main application entry point template
- `PRECOMMIT_CONTENT` - Pre-commit configuration template

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

## Package Resources

The package includes template files that are distributed with the package:

- `copilot-instructions.md` - GitHub Copilot development guidelines
- Template Python modules (copied to new projects)

## Resource Access Pattern

The package uses `importlib.resources` for accessing packaged files:

```python
try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    from importlib_resources import files

# Access package resources
package_files = files('organiseMyProjects')
copilot_file = package_files / 'copilot-instructions.md'
content = copilot_file.read_text()
```

## Testing Framework

### Test Structure

The test suite is organized into several modules:

#### `tests/conftest.py`
Shared test fixtures and configuration:
- `temp_dir` - Temporary directory fixture
- `sample_project_name` - Standard test project name
- `mock_python_file` - Sample Python file with violations

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
pytest tests/test_createProject.py::TestCreateProject::test_create_project_basic_structure
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
@patch('organiseMyProjects.createProject.subprocess.run')
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
   pip install -r dev-requirements.txt
   ```
3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Code Quality Standards

#### Formatting
- Use `black` for code formatting
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
    rev: stable
    hooks:
      - id: black
        language: system
  - repo: local
    hooks:
      - id: gui-naming-linter
        name: GUI Naming Linter
        entry: python tests/runLinter.py
        language: system
        types: [python]
```

### Release Process

1. Update version in `setup.py`
2. Update `CHANGELOG.md` (if exists)
3. Run full test suite: `pytest`
4. Run linter: `runLinter .`
5. Format code: `black .`
6. Build package: `python setup.py sdist`
7. Test installation: `pip install dist/organiseMyProjects-*.tar.gz`

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
# Add debug prints to createProject.py
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