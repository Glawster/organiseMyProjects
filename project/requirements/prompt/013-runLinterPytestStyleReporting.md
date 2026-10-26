# 013: Implement runLinter pytest-style reporting

Implement requirement 013,
[runLinter pytest-style reporting](../features/013-runLinterPytestStyleReporting.md).
The requirement is authoritative for scope and acceptance criteria 1–11.

Change `organiseMyProjects/runLinter.py` so linting collects findings as data
(relative path, line, rule identifier and rule-specific message) and a separate
reporter prints a pytest-style header, per-file progress, findings as
`<relativePath>:<line>: <ruleId> <message>` and a closing summary line. Return
exit status `0` when clean, `1` on findings, `2` for invalid invocation or
unusable targets, and `5` when nothing was linted. Do not add verbosity
switches.

Constraints:

- Do not change which rules exist or what they accept.
- Leave `runLinter --markup` behaviour and exit status unchanged.
- Implement in `runLinter.py` and `guiNamingLinter.py`, not through an
  import-time patch; the patch-removal refactor lands first.
- Fix or explicitly allow the existing findings in this repository so
  `runLinter .` exits `0`.

Allowed files: `organiseMyProjects/runLinter.py`,
`organiseMyProjects/guiNamingLinter.py`, `tests/test_runLinter.py`, the files
containing this repository's existing findings, `documentation/linter.md`,
`documentation/howToRelease.md` and `documentation/releaseNotes.md`.

Verify with:

```bash
pytest
runLinter .; echo $?
runLinter --markup
```

Hand off with the test results, sample output, observed exit
statuses, and a note of any downstream exit-status impact.
