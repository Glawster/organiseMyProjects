# 017: Clarify the requirements guide

Implement requirement 017,
[Requirements guide clarifications](../features/017-requirementsGuideClarifications.md).
The requirement is authoritative for scope and acceptance criteria 1–4.

Update `documentation/requirementsManagement.md` (and the template and
`.github/agent-instructions.md` where they restate the rules) to add the
rename-for-correction exception, define the prose reference form, clarify
external prefixes, and turn example links into code.

Constraints:

- Documentation only; no behaviour changes.
- Keep wording generic because the guide is deployed downstream.

Allowed files: `documentation/requirementsManagement.md`, `project/requirements/templates/requirement.md`, `.github/agent-instructions.md`.

Verification: run `pytest` in the `ompr` environment, `runLinter .` and
`manageProject --check`, and hand off the evidence for each acceptance
criterion.
