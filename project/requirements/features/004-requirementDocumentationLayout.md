# 004: Requirement, prompt and folder-index layout

## Status

InProgress

## Outcome

As an OMP maintainer, I need repositories to use one unambiguous Markdown
layout for the repository README, folder indexes, requirement specifications and
agent prompts so that agents create consistently named artifacts and
`manageProject --update` can safely clean up obsolete OMP-generated layouts.

## Context

OMP 0.6 adopts a deliberately simple README rule: `README.md` is reserved for
the repository root. No OMP-managed subdirectory uses `README.md` as its index
or instructions file.

Where a directory genuinely needs an index, navigation page or directory-level
instructions, the standard filename is `folderIndex.md`.

Requirements and prompts remain named artifacts rather than folder indexes:

```text
project/requirements/features/003-viewManagement.md
project/requirements/prompt/003-viewManagement.md
```

When one requirement genuinely needs multiple prompts, the established suffix
rule applies:

```text
project/requirements/prompt/003a-viewManagement.md
project/requirements/prompt/003b-viewManagement.md
```

Existing OMP repositories have used several index names over time, including
nested `README.md`, `requirementsIndex.md` and `adrIndex.md`. Agents have also
occasionally created per-requirement or per-prompt directories containing a
single `README.md`. OMP 0.6 must converge these recognisable forms safely while
preserving arbitrary user-owned or third-party content.

## Scope

### Repository README rule

- A repository has exactly one OMP-standard `README.md`, at repository root.
- The root `README.md` is the repository entry point and links to important
  living guides and indexes.
- OMP must not scaffold or recommend `README.md` in a subdirectory.
- Non-OMP third-party/vendor or user-owned nested README files must not be
  renamed or deleted merely because they conflict with the OMP convention.

### Folder index rule

- When a directory genuinely needs an index, navigation page, catalogue or
  directory-specific instructions, name it `folderIndex.md`.
- Do not create `folderIndex.md` merely because a directory exists.
- The standard OMP project-management indexes are:

  ```text
  project/requirements/folderIndex.md
  project/adr/folderIndex.md
  ```

- Generated links, managed documentation and readiness checks use these
  canonical paths.

### Canonical requirement specifications

- Every individual requirement specification is one flat file at:

  ```text
  project/requirements/features/<nnn>-<requirementName>.md
  ```

- `<nnn>` is the permanent three-digit requirement identifier.
- `<requirementName>` is the concise camelCase requirement name.
- The identifier is allocated from `project/requirements/folderIndex.md` and is
  never reused.
- The specification remains at the same path throughout its lifecycle.
- Do not create a directory for an individual requirement merely to contain a
  `README.md`, `folderIndex.md` or the specification.

### Canonical prompt files

- A requirement with one prompt uses exactly the same filename as its
  specification beneath `project/requirements/prompt/`.
- Multiple prompts use sequential lowercase suffixes on the numeric identifier
  while retaining the same requirement name.
- The unsuffixed form is used only while there is one prompt.
- If a second prompt is added later, rename the existing prompt to the `a` form,
  create `b`, and update references in the same change.
- Do not create a per-requirement prompt directory merely to contain
  `README.md`, `folderIndex.md`, `prompt.md` or another single prompt file.
- Shared support directories such as `prompt/adapters/` may use
  `folderIndex.md` only when directory-level guidance is genuinely useful.

### Managed documentation and scaffold alignment

Review and update all OMP-managed and maintainer guidance that discusses README,
indexes, requirements or ADRs. At minimum include:

- `documentation/repositoryLayout.md`;
- `documentation/requirementsManagement.md`;
- generated root README guidance;
- requirement and ADR scaffold/index guidance;
- `manageProject --check` / `agentCheck` rules and diagnostics; and
- tests and fixtures containing legacy paths.

### `manageProject --update` cleanup: folder indexes

Support deterministic migration of recognised historical OMP index names:

```text
project/requirements/README.md
project/requirements/requirementsIndex.md
    -> project/requirements/folderIndex.md

project/adr/README.md
project/adr/adrIndex.md
    -> project/adr/folderIndex.md
```

Rules:

- Migrate only when the source content has the expected OMP index shape.
- Update actual Markdown link destinations that point to the legacy path.
- Do not rewrite historical examples or ordinary prose merely because they
  mention a legacy filename.
- If `folderIndex.md` already exists with different meaningful content, preserve
  both and report the collision unless a no-loss resolution is provably safe.
- Never rename arbitrary nested README files based solely on their filename.
- Dry-run reports intended changes without modifying the working tree.
- Re-running a successful migration is idempotent.

### `manageProject --update` cleanup: erroneous requirement/prompt directories

Recognise deterministic single-artifact directory mistakes such as:

```text
project/requirements/features/003-viewManagement/
└── README.md
```

becoming:

```text
project/requirements/features/003-viewManagement.md
```

and:

```text
project/requirements/prompt/003-viewManagement/
└── README.md
```

becoming:

```text
project/requirements/prompt/003-viewManagement.md
```

A sole `prompt.md` may also be migrated when the exact requirement relationship
is independently established.

For all such cleanup:

- derive the exact `<nnn>-<requirementName>` identity before changing anything;
- preserve source and destination when differing canonical content already
  exists;
- do not flatten directories containing additional or ambiguous content;
- remove the source only after successful migration;
- remove a legacy directory only when empty; and
- keep dry-run and rerun behaviour deterministic.

## Out of scope

- Renaming or deleting third-party/vendor README files that OMP does not own.
- Renaming arbitrary user-owned README files merely to satisfy the convention.
- Creating `folderIndex.md` in every directory regardless of need.
- Renaming valid requirement specifications or prompts solely for style.
- Combining multiple requirement specifications into one file.

## Acceptance criteria

1. Managed repository guidance states that `README.md` is reserved for the
   repository root.
2. Managed guidance defines `folderIndex.md` as the standard directory index or
   directory-instructions filename when one is needed.
3. New OMP scaffolds contain no OMP-generated nested `README.md` files.
4. New OMP scaffolds use `project/requirements/folderIndex.md` and
   `project/adr/folderIndex.md` for managed indexes.
5. Requirement specifications use
   `project/requirements/features/<nnn>-<requirementName>.md`.
6. Single prompts use
   `project/requirements/prompt/<nnn>-<requirementName>.md`, with the existing
   `a`, `b`, `c` suffix convention retained for multiple prompts.
7. `manageProject --update --confirm` safely migrates recognised requirements
   indexes from both `README.md` and `requirementsIndex.md` to
   `folderIndex.md`.
8. The equivalent ADR migrations from `README.md` and `adrIndex.md` are
   supported.
9. Actual Markdown links to migrated indexes are updated without rewriting
   historical migration examples in managed guidance.
10. Dry-run reports index/artifact migrations while leaving files unchanged.
11. Existing canonical destination collisions are preserved and reported unless
    a no-loss resolution is provably safe.
12. Unrecognised/user-owned/third-party nested README files are preserved by
    update cleanup.
13. Recognisable erroneous requirement-directory and prompt-directory layouts
    are migrated to canonical flat files only when deterministic and safe.
14. Legacy directories are removed only after successful migration and only
    when empty.
15. Re-running update after successful cleanup produces no further changes.
16. `manageProject --check` recognises `folderIndex.md` and reports nested
    `README.md` as a repository-convention failure without deleting it.
17. Automated tests cover index migration, link migration, dry-run, collisions,
    user-owned README protection, requirement/prompt cleanup and idempotency.

## Dependencies and decisions

- Builds on the deterministic, ownership-safe migration policy from requirements
  001 and 003.
- Supersedes the previous OMP convention that allowed directory-specific
  `README.md` files.
- Requirement and prompt stable-ID naming remains unchanged apart from replacing
  the requirements index authority path with
  `project/requirements/folderIndex.md`.

## Verification

- Review `documentation/repositoryLayout.md` and
  `documentation/requirementsManagement.md` against this requirement.
- Search OMP-managed sources for nested `README.md` path assumptions.
- Unit tests for requirements-index and ADR-index migration.
- Unit tests for erroneous requirement/prompt directory detection and migration.
- Tests proving arbitrary user-owned nested README files are preserved.
- `manageProject --check` against a newly scaffolded repository.
- Full pytest, Ruff, Black and markup validation.

## Traceability

- Implementation: `organiseMyProjects/requirementLayout.py`,
  `organiseMyProjects/__init__.py`
- Tests: `tests/test_requirementLayout.py`, `tests/test_agentCheck.py`, existing
  scaffold/integration regression tests
- Documentation: `README.md`, `documentation/repositoryLayout.md`,
  `documentation/requirementsManagement.md`
- Pull request: pending
- Agent runs: v0.6 requirement 004 implementation

## Change history

- 2026-09-01: created after observing agents create requirement directories
  containing `README.md`.
- 2026-09-01: corrected to clarify the canonical numbered requirement
  specification path.
- 2026-09-01: expanded so prompts use matching flat filenames and erroneous
  prompt-directory forms can be cleaned safely.
- 2026-09-01: expanded repository-wide to reserve `README.md` for repository
  root and standardise directory indexes as `folderIndex.md`.
- 2026-09-01: implementation started; added safe index and artifact migrations,
  readiness checks, documentation alignment and regression coverage.
