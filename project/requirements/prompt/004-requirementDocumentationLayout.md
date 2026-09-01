# 004: Requirement, prompt and folder-index layout — implementation prompt

Requirement: `project/requirements/features/004-requirementDocumentationLayout.md`

## Role

Implement and verify requirement 004 for OMP 0.6.

## Required outcome

Make the OMP scaffold, managed guidance and update/check behaviour consistently
follow these rules:

- `README.md` is reserved for repository root;
- directory indexes or directory-specific instructions use `folderIndex.md`
  only when an index is genuinely needed;
- requirements use flat
  `project/requirements/features/<nnn>-<requirementName>.md` files;
- single prompts use matching flat
  `project/requirements/prompt/<nnn>-<requirementName>.md` files;
- multiple prompts retain the `a`, `b`, `c` numeric-suffix convention; and
- recognised legacy OMP-managed nested README/index and erroneous
  requirement/prompt directory forms are migrated safely by
  `manageProject --update`.

## Scope

Follow every scope item and acceptance criterion in requirement 004. Review at
minimum:

- `documentation/repositoryLayout.md`;
- `documentation/requirementsManagement.md`;
- `.github/agent-instructions.md` where relevant;
- `organiseMyProjects/manageProject.py`;
- `organiseMyProjects/agentCheck.py`;
- generated README/scaffold templates;
- requirement and ADR index templates;
- tests and fixtures containing nested `README.md` assumptions.

## Safety constraints

- Do not rename or remove arbitrary user-owned or third-party README files.
- Only migrate a nested README/index where OMP ownership or a deterministic
  scaffold relationship can be established.
- Preserve source and destination on ambiguous collisions.
- Do not create `folderIndex.md` in directories that do not need an index.
- Do not flatten genuine multi-file project directories.
- Dry-run must describe all intended changes without modifying the working tree.
- Confirmed migrations must be idempotent.

## Verification

Map tests to every acceptance criterion in requirement 004. Run the full OMP
suite plus Black, Ruff, OMP Python/markup lint and
`python3 -m organiseMyProjects.manageProjectCli --check` before marking the
requirement complete.

## Handoff

Report:

- files changed and why;
- requirement acceptance criteria mapped to evidence;
- migration cases covered;
- commands run and results;
- any preserved ambiguity or unresolved risk.
