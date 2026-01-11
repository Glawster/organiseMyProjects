# Additional Copilot Instructions for organiseMyProjects

## Project-Specific Information

This file contains project-specific details for the **organiseMyProjects** repository. For generic Python/Tkinter development guidelines, see `copilot-instructions.md`.

## Project Overview

**organiseMyProjects** is a Python toolkit for scaffolding new Python projects with predefined structure, logging, GUI naming conventions, and enforceable coding standards. It provides templates and tools to quickly create consistent, well-structured Python applications with Tkinter GUIs.

### Key Features
- 📁 Create full Python project scaffolds with `createProject`
- 🔄 Update existing projects with `createProject <name> --update`
- 🧪 Automatically include logging setup, dev tools, and layout
- 🧼 Run custom GUI naming linter with `runLinter`
- 🧰 Includes pre-commit support and code style guidelines
- 🤖 Includes GitHub Copilot instructions for generated projects

## Repository Structure

```
organiseMyProjects/
├── .github/
│   ├── copilot-instructions.md           # Generic guidelines (template)
│   └── additional-copilot-instructions.md # Project-specific (this file, NOT template)
├── organiseMyProjects/                    # Main package
│   ├── createProject.py                   # [PACKAGE] Project scaffolding tool
│   ├── logUtils.py                       # [PACKAGE] Centralized logging utility
│   ├── globalVars.py                     # [PACKAGE] Global constants
│   ├── copilot-instructions.md           # [TEMPLATE] Generic guidelines
│   ├── HELP.md                           # [PACKAGE] GUI linter documentation
│   ├── guiNamingLinter.py                # [TEMPLATE] Naming convention checker
│   ├── runLinter.py                      # [TEMPLATE] Linter CLI interface
│   ├── baseFrame.py                      # [TEMPLATE] Base GUI framework
│   ├── frameTemplate.py                  # [TEMPLATE] Template for new frames
│   ├── statusFrame.py                    # [TEMPLATE] Status display utilities
│   ├── styleUtils.py                     # [TEMPLATE] GUI styling utilities
│   └── mainMenu.py                       # [TEMPLATE] Main menu framework
├── tests/                                 # Test suite (not distributed)
│   ├── test_createProject.py
│   ├── test_guiNamingLinter.py
│   ├── test_runLinter.py
│   ├── test_integration.py
│   └── conftest.py
├── setup.py                               # Package configuration
├── MANIFEST.in                            # Distribution files
├── README.md                              # User documentation
├── DEVELOPER.md                           # Developer guide
└── pytest.ini                             # Test configuration
```

### File Categories

**[PACKAGE]** - Package utilities that remain in organiseMyProjects and are NOT copied to new projects:
- `createProject.py` - The scaffolding tool itself
- `logUtils.py` - Package-level logging (projects should implement their own)
- `globalVars.py` - Package constants
- `HELP.md` - Documentation

**[TEMPLATE]** - Template files that are copied to new projects:
- `copilot-instructions.md` - Generic development guidelines
- `guiNamingLinter.py` - Naming linter for the new project
- `runLinter.py` - Linter CLI for the new project
- `baseFrame.py`, `frameTemplate.py`, `statusFrame.py` - GUI framework
- `styleUtils.py` - GUI styling utilities
- `mainMenu.py` - Main menu framework

## Core Components

### createProject.py
- **Purpose**: Creates and updates Python project scaffolds
- **Key Functions**:
  - `createProject(projectName)` - Creates a new project structure
  - `updateProject(projectName)` - Updates existing project with latest templates
  - `copyIfNewer(src, dest)` - Smart file copying with timestamp checking
  - `updateTextFile(src, dest, marker)` - Merges text files with section markers
- **Resource Access**: Uses `importlib.resources` with filesystem fallback

### guiNamingLinter.py
- **Purpose**: Enforces widget naming conventions via AST analysis
- **Type**: TEMPLATE (copied to new projects' tests/ directory)
- **Key Classes**:
  - `GuiNamingVisitor` - AST visitor for analyzing code
- **Key Functions**:
  - `lintFile(filepath)` - Lint a single Python file
  - `lintGuiNaming(target)` - Lint directory recursively
- **Rules**: Enforces prefix-based naming (btn*, lbl*, frm*, etc.)

### runLinter.py
- **Purpose**: CLI interface for the naming linter
- **Type**: TEMPLATE (copied to new projects' tests/ directory)
- **Behavior**:
  - With targets: Lints specified files/directories
  - Without targets: Searches for src/, ui/, tests/ directories
  - Falls back to current directory if no project dirs found

### logUtils.py
- **Purpose**: Package-level logging utility
- **Type**: PACKAGE UTILITY (NOT copied to new projects)
- **Note**: New projects should implement their own logging based on their needs

## Package Distribution

### Distribution Strategy

The package contains two types of files:

1. **Package Utilities** - Stay in the organiseMyProjects package:
   - `createProject.py` - The tool that creates/updates projects
   - `logUtils.py` - Package-level logging (not distributed to projects)
   - `globalVars.py` - Package constants
   
2. **Template Files** - Copied to new projects via `createProject`:
   - `copilot-instructions.md` - Generic Copilot guidelines
   - `guiNamingLinter.py` - Naming checker for the project
   - `runLinter.py` - Linter CLI for the project
   - GUI framework files: `baseFrame.py`, `frameTemplate.py`, `statusFrame.py`, `mainMenu.py`, `styleUtils.py`

### Technical Details
- Tests excluded from package via `setup.py` (not installed)
- Template files included via `MANIFEST.in`
- Uses `importlib.resources` for accessing packaged files
- Fallback to filesystem for development mode

### Entry Points
- `createProject` - Command to create/update projects
- `runLinter` - Command to run GUI naming linter

### Resource Access Pattern
```python
try:
    from importlib.resources import files
    template = files('organiseMyProjects') / 'template.py'
    content = template.read_text()
except (ImportError, FileNotFoundError):
    # Fallback for development mode
    template = Path(__file__).parent / 'template.py'
    content = template.read_text()
```

## Development Workflow

### Setup
```bash
# Clone repository
git clone https://github.com/Glawster/organiseMyProjects.git
cd organiseMyProjects

# Install in development mode
pip install -e .

# Install dev dependencies
pip install pytest black
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_createProject.py

# Run with verbose output
python -m pytest -v

# Run with coverage
python run_tests.py --coverage
```

### Linting and Formatting
```bash
# Format code
black organiseMyProjects/ tests/

# Run GUI naming linter
python -m organiseMyProjects.runLinter organiseMyProjects/
```

### Testing Project Creation
```bash
# Create a test project
createProject testProject

# Update an existing project
createProject testProject --update

# Or from within project directory
cd testProject
createProject --update
```

## Test Suite Details

### Test Organization
- `test_createProject.py` - 12 tests for project scaffolding
- `test_guiNamingLinter.py` - 36 tests for linter logic
- `test_runLinter.py` - 10 tests for CLI interface
- `test_integration.py` - 12 tests for end-to-end workflows
- **Total**: 70+ comprehensive tests

### Test Patterns
- Use `tmp_path` for temporary directories (automatic cleanup)
- Mock `lintGuiNaming` in CLI tests to avoid actual linting
- Change working directory for tests that depend on CWD
- Provide descriptive assertion messages for debugging

### Key Test Cases
- Project structure creation
- File timestamp handling
- Widget naming rule validation
- CLI argument parsing
- Package resource access
- Update functionality
- Error handling

## Code Review Checklist (Project-Specific)

Before submitting changes:
- [ ] All 70+ tests pass: `python -m pytest`
- [ ] Code formatted: `black organiseMyProjects/ tests/`
- [ ] Linter passes: `runLinter organiseMyProjects/`
- [ ] Test project creation: `createProject testProject`
- [ ] Test project update: `createProject testProject --update`
- [ ] Package distribution works: `python setup.py sdist`
- [ ] Entry points work after install: `createProject --help`, `runLinter --help`
- [ ] Documentation updated for new features
- [ ] Backward compatibility maintained
- [ ] Cross-platform functionality verified (if possible)

## Common Development Tasks

### Adding a New Template File
1. Add file to `organiseMyProjects/` directory
2. Update `MANIFEST.in` if needed
3. Update `createProject()` to copy the file
4. Add test in `test_createProject.py`
5. Update README.md with file description

### Adding a New Widget Type to Linter
1. Add naming rule to `NAMING_RULES` dict in `guiNamingLinter.py`
2. Add widget class to `WIDGET_CLASSES` set
3. Add parametrized test cases in `test_guiNamingLinter.py`
4. Update HELP.md and copilot-instructions.md

### Modifying Project Structure
1. Update `createProject()` function
2. Update tests to verify new structure
3. Update README.md documentation
4. Consider backward compatibility for `updateProject()`

## Troubleshooting

### Tests Failing on Windows
- Check path separators (use `Path` from `pathlib`)
- Verify working directory changes in tests
- Check for platform-specific file handling

### Package Distribution Issues
- Verify `MANIFEST.in` includes all necessary files
- Check `setup.py` excludes tests properly
- Test with `python setup.py sdist` and inspect generated tarball

### Import Errors After Install
- Ensure entry points are correctly defined in `setup.py`
- Verify package name matches import statements
- Check that `__init__.py` files are present where needed

## Future Considerations

### Potential Enhancements
- Add more template variations (CLI-only, no-GUI, etc.)
- Support for other GUI frameworks (PyQt, wxPython)
- Configuration file for customizing generated projects
- Plugin system for custom linter rules
- Better handling of existing projects during updates

### Maintenance Notes
- Keep `copilot-instructions.md` generic and reusable
- Update this file for project-specific changes
- Maintain backward compatibility in `updateProject()`
- Keep test coverage above 90%
