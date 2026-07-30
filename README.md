# organiseMyProjects

A Python toolkit to scaffold new projects with predefined structure, logging, GUI naming conventions, and enforceable coding standards.

## Documentation

The README is the canonical entry point for repo documentation. The living guides are:

- [Developer Guide](documentation/developer.md)
- [Git Guide](documentation/git.md)
- [GUI Naming Linter Help](organiseMyProjects/HELP.md)
- [Master Agent Instructions](.github/agent-instructions.md)
- [Copilot Compatibility Instructions](.github/copilot-instructions.md)
- [Repository Layout](.github/repositoryLayout.md)
- [Requirements Management](.github/requirementsManagement.md)
- [Repository Agent Notes](.github/additional-instructions.md)

## Features

- 📁 Create a full Python project scaffold using `createProject`
- 🔄 Update an existing scaffold with `createProject <name> --update` or run
  `createProject --update` inside the project directory
- 🧪 Automatically include logging setup, dev tools, and layout
- 🧼 Run a custom GUI naming linter with `runLinter` (default scans the current project)
- 🧰 Includes pre-commit support and code style guidelines
- 🤖 Includes AI coding agent instructions for consistent development guidelines

## Installation

```bash
pip install .
```

## Usage

### Create a new project
```bash
createProject myNewProject
```

Optional UI scaffolds can be installed at creation time:

```bash
# add the tkinter starter package
createProject myNewProject --ui

# add the Qt/PySide6 starter package
createProject myNewProject -qt

# install both UI scaffolds
createProject myNewProject --ui -qt
```

Creates:
```
myNewProject/
├── AGENTS.md                   # Agent discovery and instruction entry point
├── .github/
│   ├── agent-instructions.md    # Canonical AI coding agent guidelines
│   ├── copilot-instructions.md  # Generated GitHub Copilot compatibility copy
│   ├── repositoryLayout.md      # Project file and directory placement rules
│   └── requirementsManagement.md # Shared requirements workflow
├── src/
│   ├── __init__.py
│   └── globalVars.py              # Project constants template
├── ui/
│   ├── __init__.py
│   ├── mainMenu.py               # Main application entry point
│   ├── baseFrame.py              # Base GUI framework
│   ├── frameTemplate.py          # Template for new frames
│   ├── statusFrame.py            # Status display utilities
│   └── styleUtils.py             # GUI styling utilities
├── tests/
│   └── runLinter.py              # Linter entry point
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
Refresh a project scaffold and replace missing scaffold files. Managed
instructional/config files such as `pytest.ini`, `.pre-commit-config.yaml`,
`.vscode/settings.json`, `tests/runLinter.py`, and Agent instructions are
refreshed in place, while project-owned code such as `main.py`, `.env`,
`requirements.txt`, and UI/Qt modules is only created when missing. Provide the
project name or run inside the target directory:
```bash
# from anywhere
createProject myExistingProject --update

# or from within the project directory
createProject --update

# add tkinter or Qt scaffolds during update
createProject myExistingProject --update --ui
createProject myExistingProject --update -qt
```

`createProject --update` no longer creates dated backup copies. If you want to
undo scaffold refresh changes, inspect the changed files in VS Code's Source
Control/Changed Files view and revert the files you do not want before
committing.

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
pytest tests/test_CreateProject.py

# Run with verbose output
pytest -v

# Run with coverage (if pytest-cov is installed)
pytest --cov=organiseMyProjects
```

### Test Structure
- `tests/test_CreateProject.py` - Tests for project creation and updating
- `tests/test_GuiNamingLinter.py` - Tests for GUI naming convention linting
- `tests/test_RunLinter.py` - Tests for the linter CLI interface
- `tests/test_Integration.py` - End-to-end integration tests
- `tests/test_LogUtils.py` - Tests for logging utilities (including `drawBox`)
- `tests/test_SyncAgentInstructions.py` - Tests for Agent instructions sync
- `tests/conftest.py` - Shared test fixtures and configuration

**Note**: The `tests/` directory is for development and testing of this project itself. It is not included in the installed package, so end users won't get these test files when they install `organiseMyProjects`.

## Development

### Running Tests
```bash
# Install development dependencies
pip install pytest black

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
- `.github/agent-instructions.md` - Master AI coding agent development guidelines
- Template files for GUI components and utilities

### Sync Agent Instructions to other repos

`organiseMyProjects` is the single source of truth for `.github/agent-instructions.md`.
`.github/copilot-instructions.md` is an identical compatibility copy for GitHub
Copilot. Use `syncAgentInstructions.py` to push both instruction paths to all
downstream Glawster repos. The same routine distributes the canonical
repository layout to `.github/repositoryLayout.md` and the requirements guide
to `.github/requirementsManagement.md`.

Without `--repo`, every eligible repository is processed. `--repo` with no
value opens a numbered selector; supplying a repository name avoids the prompt
and is suitable for scripts.

```bash
# Preview what would change (dry-run, default)
python syncAgentInstructions.py

# Choose one repository from a numbered list
python syncAgentInstructions.py --repo

# Select one repository non-interactively
python syncAgentInstructions.py --repo Glawster/myRepository

# Actually push updates
GITHUB_TOKEN=<your-pat> python syncAgentInstructions.py --confirm

# Actually update one repository selected from the list
GITHUB_TOKEN=<your-pat> python syncAgentInstructions.py --repo --confirm

# Push updates, then create and merge conflict-free pull requests
GITHUB_TOKEN=<your-pat> python syncAgentInstructions.py --confirm --merge

# Pass the token directly and show extra detail
python syncAgentInstructions.py --confirm --token <your-pat> --verbose
```

Requires a GitHub Personal Access Token with `repo` scope. Supply it once via
the `GITHUB_TOKEN` environment variable or the `--token` flag. The script saves
it with user-only permissions in
`~/.config/organiseMyProjects/syncAgentInstructions.json` and uses that value
on future runs. An explicitly supplied token takes precedence over the stored
value and refreshes it.

## License

This project is licensed under the [MIT License](LICENSE).
