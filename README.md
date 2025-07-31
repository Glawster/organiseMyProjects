# organiseMyProjects

A Python toolkit to scaffold new projects with predefined structure, logging, GUI naming conventions, and enforceable coding standards.

## Features

- 📁 Create a full Python project scaffold using `createProject`
<<<<<<< HEAD
- 🔄 Update an existing scaffold with `createProject <name> --update` or run
  `createProject --update` inside the project directory
=======
- 🔄 Update an existing scaffold with `createProject <name> --update`
>>>>>>> main
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