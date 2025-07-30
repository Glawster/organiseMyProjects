# organiseMyProjects

A Python toolkit to scaffold new projects with predefined structure, logging, GUI naming conventions, and enforceable coding standards.

## Features

- 📁 Create a full Python project scaffold using `createProject`
- 🧪 Automatically include logging setup, dev tools, and layout
- 🧼 Run a custom GUI naming linter with `runLinter`
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

### Run the GUI naming linter
```bash
runLinter <file_or_dir>
```

Checks for violations of variable/class naming and logging message style.

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
