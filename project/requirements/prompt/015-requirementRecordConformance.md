# 015: Implement requirement record conformance checks

Implement requirement 015,
[Requirement record conformance checks](../features/015-requirementRecordConformance.md).
The requirement is authoritative for scope and acceptance criteria 1–7.

Extend `agentCheck._checkRequirementsAndAdrs` so requirement filenames,
headings, required sections, index Req IDs and prompt locations are checked
against `documentation/requirementsManagement.md`. Rows, statuses and prompt
links that cannot be parsed must produce findings instead of being skipped.
Give each new finding a stable rule ID.

Constraints:

- Report only; do not change files (requirement 016 corrects).
- Keep existing REQ-001 to REQ-005 behaviour for conforming repositories.

Allowed files: `organiseMyProjects/agentCheck.py`, `tests/test_agentCheck.py` or a new focused test module, and documentation of the new rule IDs.

Verification: run `pytest` in the `ompr` environment, `runLinter .` and
`manageProject --check`, and hand off the evidence for each acceptance
criterion.
