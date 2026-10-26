# 020: Implement documentation completeness checks

Implement requirement 020,
[Documentation completeness checks](../features/020-documentationCompletenessChecks.md).
The requirement is authoritative for scope and acceptance criteria 1–4.

Add checks that every guide under `documentation/` is linked from the README
Documentation section and that `.github/additional-instructions.md` no longer
contains the scaffold placeholders. Record the decision on how OMPR-deployed
guides are listed in the requirement before implementing.

Constraints:

- Report only; do not write documentation.

Allowed files: `organiseMyProjects/agentCheck.py` and its tests.

Verification: run `pytest` in the `ompr` environment, `runLinter .` and
`manageProject --check`, and hand off the evidence for each acceptance
criterion.
