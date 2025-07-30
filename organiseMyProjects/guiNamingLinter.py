"""
guiNamingLinter.py - GUI Code Quality Linter

This linter enforces project-specific guidelines for Python GUI development:
- Function formatting (blank line after def if >4 statements)
- Widget naming conventions
- Constant and variable naming rules
- Logging message formatting
- Misspelling detection (e.g., 'iCloud')
"""

import ast
import os
import re

# Naming rules for GUI elements and handlers
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

# Allow patterns or names to bypass class rule
classNameExceptions = {'iCloudSyncFrame'}
classNamePatterns = [r'^iCloud[A-Z]\w*']

widgetClasses = set(namingRules.keys()) - {'Handler', 'Constant', 'Class'}

class GuiNamingVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
        self.packCalls = 0
        self.gridCalls = 0

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            varName = node.targets[0].id

            if isinstance(node.value, (ast.Num, ast.Str, ast.Constant, ast.List, ast.Tuple)):
                if isinstance(getattr(node, 'parent', None), ast.Module):
                    if not re.match(namingRules['Constant'], varName):
                        self.violations.append((varName, 'Constant', node.lineno))

        if isinstance(node.value, ast.Call):
            try:
                widgetType = node.value.func.attr if isinstance(node.value.func, ast.Attribute) else None
                if widgetType in widgetClasses:
                    varName = node.targets[0].id
                    pattern = namingRules[widgetType]
                    if not re.match(pattern, varName):
                        self.violations.append((varName, widgetType, node.lineno))
            except AttributeError:
                pass

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Rule: If function body has >4 statements, expect a blank line after def
        if len(node.body) > 4:
            next_line = getattr(node.body[0], 'lineno', None)
            if next_line and next_line == node.lineno + 1:
                self.violations.append((node.name, 'Function spacing (no blank line after def)', node.lineno))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        isExplicitlyAllowed = node.name in classNameExceptions
        isPatternAllowed = any(re.match(pat, node.name) for pat in classNamePatterns)
        if not (isExplicitlyAllowed or isPatternAllowed):
            if not re.match(namingRules['Class'], node.name):
                self.violations.append((node.name, 'Class', node.lineno))
        self.generic_visit(node)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute):
                if func.attr == 'pack':
                    self.packCalls += 1
                elif func.attr == 'grid':
                    self.gridCalls += 1

                if func.attr in {'info', 'warning', 'error'}:
                    if node.value.args and isinstance(node.value.args[0], ast.Constant):
                        msg = node.value.args[0].value
                        if func.attr in {'info', 'warning'}:
                            if not msg.islower() and not re.match(r'[.]{3}.*|.*[.]{3}|[.]{3}.*:.*', msg):
                                self.violations.append((msg, f"Logging ({func.attr})", node.lineno))
                        elif func.attr == 'error':
                            if msg != msg.capitalize():
                                self.violations.append((msg, 'Logging (error)', node.lineno))

        if isinstance(node.value, ast.Constant):
            val = node.value.value
            if isinstance(val, str):
                icloudMatches = re.findall(r'\b[iI][cC]loud\b', val)
                for match in icloudMatches:
                    if match != 'iCloud':
                        self.violations.append((match, 'Spelling (iCloud)', node.lineno))

        self.generic_visit(node)

def annotateParents(tree):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

def checkFile(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=filepath)
        annotateParents(tree)
        visitor = GuiNamingVisitor()
        visitor.visit(tree)
        if visitor.gridCalls > 0 and visitor.packCalls == 0:
            visitor.violations.append(("layout", "Use 'pack()' instead of 'grid()'", 0))
        return visitor.violations

def lintGuiNaming(directory):
    print(f"\nChecking GUI naming in: {directory}\n" + "-"*50)
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.py'):
                path = os.path.join(root, filename)
                violations = checkFile(path)
                if violations:
                    print(f"\n{filename}:")
                    for name, ruleType, lineno in violations:
                        print(f"  Line {lineno}: '{name}' should follow naming rule for {ruleType}.")
                else:
                    print(f"{filename}: OK")
def lintFile(filepath):
    print(f"\nLinting: {filepath}\n" + "-"*50)
    violations = checkFile(filepath)
    if violations:
        for name, ruleType, lineno in violations:
            print(f"  Line {lineno}: '{name}' should follow naming rule for {ruleType}.")
    else:
        print("  OK")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        lintFile(sys.argv[1])
    else:
        print("Usage: python guiNamingLinter.py <script.py>")
