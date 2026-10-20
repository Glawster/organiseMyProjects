# 016: Implement requirement naming correction during update

Implement requirement 016,
[Requirement naming correction during update](../features/016-requirementNamingCorrection.md).
The requirement is authoritative for scope and acceptance criteria 1–7.

Add a deterministic correction step to `manageProject --update` that renames
non-conforming requirement and prompt files, moves prompts into
`project/requirements/prompt/`, normalises headings and status sections, and
rewrites Markdown links. Reproduce the `mailAgent` correction in commit
`ff5cb72` as the reference fixture.

Constraints:

- Dry-run by default; `--confirm` applies; reruns are no-ops.
- Use `git mv` for tracked files; never overwrite a different destination.
- List, but do not rewrite, non-link mentions of old IDs.

Allowed files: `organiseMyProjects/requirementLayout.py`, `organiseMyProjects/manageProject.py`, focused tests and fixtures.

Verification: run `pytest` in the `ompr` environment, `runLinter .` and
`manageProject --check`, and hand off the evidence for each acceptance
criterion.
