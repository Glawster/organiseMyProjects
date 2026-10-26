# 018: Implement framework override naming exemptions

Implement requirement 018,
[Framework override naming exemptions beyond Textual](../features/018-frameworkOverrideNamingExemptions.md).
The requirement is authoritative for scope and acceptance criteria 1–5.

Extend `GuiNamingLinter.functionIsNamingExempt` so methods overriding a
method of an externally imported base class are exempt, with a reviewable list
of known standard-library protocol names as a fallback.

Constraints:

- Keep requirement 007's Textual behaviour unchanged.
- Never exempt project-defined snake_case methods or module functions.

Allowed files: `organiseMyProjects/guiNamingLinter.py`, its tests, and the linter guidance.

Verification: run `pytest` in the `ompr` environment, `runLinter .` and
`manageProject --check`, and hand off the evidence for each acceptance
criterion.
