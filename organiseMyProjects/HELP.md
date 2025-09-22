# GUI Naming Linter Help

This tool checks Python GUI code for compliance with common readability and consistency standards used in the organiseMyProjects framework.

## Overview

The GUI Naming Linter enforces coding standards that improve code readability and maintainability for Python GUI applications. It checks for proper naming conventions, code formatting, and other best practices.

## Coding Standards

### Variable and Function Naming
- **camelCase** for variables and functions (except `photos.py` which uses snake_case for pyicloud compatibility)
- Examples: `processFiles`, `userName`, `calculateTotal`

### File Naming
- File names use **camelCase** (e.g., `displayContactSheet.py`, `mainFrame.py`)

### Class Naming
- **PascalCase** for class names (e.g., `MainFrame`, `ContactSheetFrame`, `DataProcessor`)

### GUI Element Prefixes
The linter enforces specific prefixes for GUI elements to make code more readable:

- **Buttons**: `btn` prefix (e.g., `btnSubmit`, `btnCancel`, `btnSave`)
- **Labels**: `lbl` prefix (e.g., `lblStatus`, `lblInfo`, `lblError`)
- **Entry fields**: `entry` prefix (e.g., `entryName`, `entryPassword`, `entryFolder`)
- **Frames**: `frm` prefix (e.g., `frmContainer`, `frmMain`, `frmSettings`)
- **Text widgets**: `txt` prefix (e.g., `txtContent`, `txtNotes`, `txtDescription`)
- **Listboxes**: `lst` prefix (e.g., `lstFiles`, `lstOptions`, `lstResults`)
- **Checkboxes**: `chk` prefix (e.g., `chkEnabled`, `chkVisible`, `chkDryRun`)
- **Radio buttons**: `rdo` prefix (e.g., `rdoOption1`, `rdoChoice`, `rdoMode`)
- **Comboboxes**: `cmb` prefix (e.g., `cmbSource`, `cmbDestination`, `cmbFormat`)

### Event Handler Naming
- Handler functions use the `on` prefix (e.g., `onSaveClick`, `onSelectionChange`, `onWindowClose`)

### Constants
- **UPPERCASE_WITH_UNDERSCORES** for constants (e.g., `WINDOW_WIDTH`, `MAX_RETRIES`, `DEFAULT_TIMEOUT`)

### Logging Standards
- Log messages should be lowercase except for ERROR messages (which use Sentence Case)
- Use consistent format patterns:
  - `"...message"` for ongoing steps
  - `"message..."` when a step is done
  - `"...key: value"` for reporting variables

## What It Checks

### Function Formatting
- **Blank line requirement**: Functions with more than 4 logical lines must have a blank line after the `def` line
- This improves readability for longer functions

Example:
```python
# Correct - short function
def shortMethod(self):
    pass

# Correct - long function with blank line
def longerMethod(self):

    line1 = "statement"
    line2 = "statement"
    line3 = "statement"
    line4 = "statement"
    line5 = "statement"

# Incorrect - long function without blank line
def badMethod(self):
    line1 = "statement"  # Violation: missing blank line after def
    line2 = "statement"
    line3 = "statement"
    line4 = "statement"
    line5 = "statement"
```

### UI Layout Checks
- Detects if `statusLabel` and `progressBar` are placed in the same grid cell with identical layout settings
- Ensures proper widget placement and prevents layout conflicts

### Widget Naming Conventions
- Enforces consistent naming for all GUI widgets
- Checks that widget variable names match their types
- Validates that naming patterns are followed correctly

### Class Name Validation
- Ensures class names follow PascalCase convention
- Handles special exceptions (e.g., `iCloudSyncFrame` for iCloud-related classes)
- Supports pattern-based exceptions for specific naming needs

### Constant Validation
- Verifies that constants use UPPER_CASE_WITH_UNDERSCORES format
- Distinguishes between constants and regular variables

## Usage

### Command Line Interface
Run the linter from the command line:

```bash
# Lint current project (searches for src/, ui/, tests/ directories)
runLinter

# Lint specific file
runLinter path/to/your_script.py

# Lint specific directory
runLinter path/to/directory

# Lint multiple targets
runLinter file1.py directory2/ file3.py
```

### Integration with Development Workflow

#### Pre-commit Hooks
The linter is automatically integrated with pre-commit hooks in generated projects:
```yaml
- repo: local
  hooks:
    - id: gui-naming-linter
      name: GUI Naming Linter
      entry: python tests/runLinter.py
      language: system
      types: [python]
```

#### IDE Integration
You can integrate the linter with your IDE by configuring it to run `runLinter` on save or as part of your build process.

### Exit Codes
- `0`: No violations found
- `1`: Violations found or error occurred

## Output Format

The linter provides detailed output about violations found:

```
Checking GUI naming in: /path/to/project
--------------------------------------------------
file1.py: OK
file2.py:
  Line 15: 'save_button' should follow naming rule for Button.
  Line 23: 'status_label' should follow naming rule for Label.
file3.py:
  Line 8: Function with >4 statements should have blank line after def.
```

### Output Sections
- **File status**: Shows "OK" for files with no violations
- **Line numbers**: Exact location of each violation
- **Violation type**: Description of what rule was violated
- **Suggested fix**: Indicates what naming convention should be followed

## Configuration

### Exceptions and Special Cases
The linter includes built-in exceptions for certain cases:
- `iCloudSyncFrame` and similar iCloud-related class names
- Pattern-based exceptions for specific naming requirements

### Extending the Linter
To add new rules or modify existing ones, edit the `guiNamingLinter.py` file:
- Add new patterns to the `namingRules` dictionary
- Modify the `GuiNamingVisitor` class to implement new checks
- Update exception lists as needed

## Best Practices

### Widget Naming Tips
1. **Be descriptive**: `btnSaveFile` is better than `btnSave`
2. **Be consistent**: Use the same prefix pattern throughout your project
3. **Avoid abbreviations**: `lblErrorMessage` is better than `lblErrMsg`
4. **Group related widgets**: `frmUserInfo`, `lblUserName`, `entryUserName`

### Function Naming Tips
1. **Use verbs**: `processData()`, `validateInput()`, `displayResults()`
2. **Be specific**: `saveUserPreferences()` is better than `save()`
3. **Event handlers**: Always start with `on` - `onButtonClick()`, `onWindowClose()`

### Code Organization Tips
1. **Group constants**: Keep all constants at the top of files
2. **Consistent indentation**: Follow PEP 8 guidelines
3. **Clear separation**: Use blank lines to separate logical sections

## Troubleshooting

### Common Issues

#### False Positives
If the linter reports violations that you believe are incorrect:
1. Check if the naming follows the exact pattern requirements
2. Verify that the widget type is correctly identified
3. Consider if an exception should be added for your use case

#### Performance Issues
For large codebases:
1. Lint specific directories instead of entire projects
2. Use the linter in CI/CD rather than on every save
3. Focus on new files rather than legacy code

#### Integration Issues
If the linter doesn't work with your development setup:
1. Ensure Python path includes the package
2. Verify that all dependencies are installed
3. Check that the entry point is correctly configured

### Getting Help
- Check the project documentation in `README.md`
- Review developer documentation in `DEVELOPER.md`
- Run tests to verify installation: `pytest tests/`

## Technical Details

### Requirements
- Python 3.7+
- AST parsing capabilities (built into Python)
- No external dependencies for core functionality

### Implementation
- Uses Python's `ast` module for parsing Python code
- Implements visitor pattern for traversing syntax trees
- Regex-based pattern matching for naming conventions
- File system traversal for directory scanning

### Performance
- Fast scanning: Processes typical GUI files in milliseconds
- Memory efficient: Processes files one at a time
- Scalable: Handles projects with hundreds of files

This linter is designed to be a helpful tool for maintaining code quality and consistency across Python GUI projects. It should be used as part of a comprehensive code quality strategy that includes testing, documentation, and code review.
