# GUI Naming Linter Help

This tool checks Python GUI code for compliance with common readability and consistency standards.

# Coding Standards

- **camelCase** for variables and functions (except `photos.py` which uses snake_case for pyicloud compatibility)
- File names use **camelCase** (e.g., `displayContactSheet.py`, `mainFrame.py`)
- GUI element prefixes:
  - `btnSubmit`, `lblStatus`, `entryFolder`, `frmContainer`, etc.
- Handler naming uses the `on` prefix (e.g., `onSaveClick`)
- Log messages lowercase except ERRORs (Sentence Case)

## ✅ What It Checks

- **Function formatting**: functions with >4 logical lines must have a blank line after the def line.
- **UI layout**: detects if `statusLabel` and `progressBar` are placed in the same grid cell with identical layout settings.
- **Widget naming conventions**: ensures naming consistency for buttons, labels, and more.

## 🚀 Usage

### CLI
Run this from the command line:
```bash
runLinter path/to/your_script.py
```

## 📋 Output
The linter will report:
- Line number
- Type of violation
- Function or widget name where applicable

## 🛠 Notes
- Ensure Python 3.9+ is installed.
- Add more checks to `guiNamingLinter.py` as your project grows.
