# organiseMyProjects

A Python toolkit to scaffold new projects with predefined structure, logging, GUI naming conventions, and enforceable coding standards.

## Features

- 📁 Create a full Python project scaffold using `createProject`
- 🔄 Update an existing scaffold with `createProject <name> --update` or run
  `createProject --update` inside the project directory
- 🧪 Automatically include logging setup, dev tools, and layout
- 🧼 Run a custom GUI naming linter with `runLinter` (default scans the current project)
- 🧰 Includes pre-commit support and code style guidelines
- 🤖 Includes GitHub Copilot instructions for consistent development guidelines

## Installation

```bash
pip install .
```

## Usage

### Create a new project
```bash
createProject myNewProject
```

Creates:
```
myNewProject/
├── .github/
│   └── copilot-instructions.md    # GitHub Copilot development guidelines
├── src/
│   ├── __init__.py
│   └── logUtils.py                # Centralized logging utilities
├── ui/
│   ├── __init__.py
│   ├── mainMenu.py               # Main application entry point
│   ├── baseFrame.py              # Base GUI framework
│   ├── frameTemplate.py          # Template for new frames
│   ├── statusFrame.py            # Status display utilities
│   └── styleUtils.py             # GUI styling utilities
├── tests/
│   ├── runLinter.py              # Linter entry point
│   └── guiNamingLinter.py        # GUI naming convention checker
├── logs/                         # Application log directory
├── main.py                       # Application main entry point
├── requirements.txt              # Production dependencies
├── dev-requirements.txt          # Development dependencies
├── .gitignore                    # Git ignore patterns
├── .env                          # Environment configuration
├── .pre-commit-config.yaml       # Pre-commit hooks configuration
└── README.md                     # Project documentation
```

### Update an existing project
Refresh a project scaffold and replace any missing or outdated files. Provide the
project name or run inside the target directory:
```bash
# from anywhere
createProject myExistingProject --update

# or from within the project directory
createProject --update
```

### Run the GUI naming linter
```bash
# lint the whole project from its root
runLinter

# or specify a file or directory
runLinter <file_or_dir>
```

Checks for violations of variable/class naming and logging message style.

### Launch the generated application
After creating a project, install its dependencies and run the starter script:
```bash
cd myNewProject
pip install -r requirements.txt
pip install -r dev-requirements.txt  # for development tools
python main.py
```

## Testing

The project includes a comprehensive test suite using pytest for **development and validation of this project**. These tests are not part of the distributed package but are used to ensure the reliability of the project scaffolding and linting functionality.

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_createProject.py

# Run with verbose output
pytest -v

# Run with coverage (if pytest-cov is installed)
pytest --cov=organiseMyProjects
```

### Test Structure
- `tests/testCreateProject.py` - Tests for project creation and updating
- `tests/testGuiNamingLinter.py` - Tests for GUI naming convention linting
- `tests/testRunLinter.py` - Tests for the linter CLI interface
- `tests/testIntegration.py` - End-to-end integration tests
- `tests/testLogUtils.py` - Tests for logging utilities (including `drawBox`)
- `tests/conftest.py` - Shared test fixtures and configuration

**Note**: The `tests/` directory is for development and testing of this project itself. It is not included in the installed package, so end users won't get these test files when they install `organiseMyProjects`.

## Development

### Running Tests
```bash
# Install development dependencies
pip install -r dev-requirements.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=organiseMyProjects --cov-report=html
```

### Code Quality
The project uses several tools to maintain code quality:

- **Black**: Automatic code formatting
- **pytest**: Comprehensive test suite
- **pre-commit**: Git hooks for quality checks
- **Custom GUI Linter**: Enforces GUI naming conventions

### Pre-commit Hooks
After creating a project, pre-commit hooks are automatically installed to:
- Format code with Black
- Run the custom GUI naming linter
- Ensure code quality before commits

## Project Guidelines

### Naming Conventions
- **Functions and Variables**: camelCase (e.g., `processFiles`, `userName`)
- **Classes**: PascalCase (e.g., `MainFrame`, `ContactSheetFrame`)
- **Constants**: UPPERCASE_WITH_UNDERSCORES (e.g., `WINDOW_WIDTH`, `MAX_RETRIES`)
- **GUI Components**: Prefixed naming (e.g., `btnSave`, `lblStatus`, `frmMain`)

### GUI Component Prefixes
- `btn` - Buttons (`btnSave`, `btnCancel`)
- `lbl` - Labels (`lblStatus`, `lblInfo`)
- `frm` - Frames (`frmMain`, `frmSettings`)
- `entry` - Entry fields (`entryName`, `entryPassword`)
- `txt` - Text widgets (`txtContent`, `txtNotes`)
- `chk` - Checkboxes (`chkEnabled`, `chkVisible`)
- `cmb` - Comboboxes (`cmbSource`, `cmbDestination`)
- `hrz` - Horizontal widgets (`hrzSpacer`, `hrzLayout`)
- `vrt` - Vertical widgets (`vrtSpacer`, `vrtLayout`)

### Logging Standards
- Use centralized logger from `logUtils.py`
- All log messages in lowercase except ERROR messages
- Format patterns:
  - `"...message"` for ongoing steps
  - `"message..."` when a step is done
  - `"...key: value"` for reporting variables

## Requirements

- Python 3.7+
- Windows with Outlook (for `pywin32`-dependent projects)
- Development tools:
  - `pywin32`
  - `black`
  - `pytest`
  - `pre-commit`

## Package Structure

The `organiseMyProjects` package includes:
- `createProject.py` - Main project scaffolding functionality
- `guiNamingLinter.py` - GUI naming convention enforcement
- `runLinter.py` - Command-line interface for the linter
- `copilot-instructions.md` - GitHub Copilot development guidelines
- Template files for GUI components and utilities

### Sync Copilot Instructions to other repos

`organiseMyProjects` is the single source of truth for `.github/copilot-instructions.md`.
Use `syncCopilotInstructions.py` to push the canonical template to all downstream Glawster repos.

```bash
# Preview what would change (dry-run, default)
python syncCopilotInstructions.py

# Actually push updates
GITHUB_TOKEN=<your-pat> python syncCopilotInstructions.py --confirm

# Pass the token directly and show extra detail
python syncCopilotInstructions.py --confirm --token <your-pat> --verbose
```

Requires a GitHub Personal Access Token with `repo` scope, supplied via the
`GITHUB_TOKEN` environment variable or the `--token` flag.

## License

This project is licensed under the [MIT License](LICENSE).