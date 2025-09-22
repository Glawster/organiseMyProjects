# organiseMyProjects

A Python toolkit to scaffold new projects with predefined structure, logging, GUI naming conventions, and enforceable coding standards.

## Features

- 📁 Create a full Python project scaffold using `createProject`
- 🔄 Update an existing scaffold with `createProject <name> --update` or run
  `createProject --update` inside the project directory
- 🧪 Automatically include logging setup, dev tools, and layout
- 🧼 Run a custom GUI naming linter with `runLinter` (default scans the current project)
- 🧰 Includes pre-commit support and code style guidelines

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
├── .github
│   └── copilot-instructions.md
├── src/
│   └── logUtils.py
├── main.py
├── ui/
│   ├── mainMenu.py
│   ├── baseFrame.py
│   ├── frameTemplate.py
│   ├── statusFrame.py
│   └── styleUtils.py
├── tests/
│   ├── runLinter.py
│   └── guiNamingLinter.py
├── logs/
├── requirements.txt
├── dev-requirements.txt
├── .gitignore
├── README.md
├── projectGuidelines.md
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
python main.py
```

## Requirements

- Python 3.7+
- Windows with Outlook (for `pywin32`-dependent projects)
- Tools:
  - `pywin32`
  - `black`
  - `pytest`
  - `pre-commit`

## License

This project is licensed under the [MIT License](LICENSE).