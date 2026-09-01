# 004: Requirement, prompt and directory-index layout

## Status

InProgress

## Outcome

As an OMP maintainer, I need repositories to use one unambiguous Markdown
layout for the repository README, directory indexes, requirement specifications
and agent prompts so that agents create consistently named artifacts and
`manageProject --update` can safely clean up obsolete OMP-generated layouts.

## Context

OMP 0.6 reserves `README.md` for the repository root. OMP-managed
subdirectories do not use `README.md` as an index or instruction file.

When a directory genuinely needs an index, the index filename is derived from
the directory name using `<folderName>Index.md`.

Examples:

```text
project/requirements/requirementsIndex.md
project/adr/adrIndex.md
```

This does not mean every directory must have an index. An index is created only
where it has a real navigation, catalogue or authority role.

Requirements and prompts remain named flat artifacts rather than directory
indexes:

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

## Scope

### Repository README rule

- A repository has exactly one OMP-standard `README.md`, at repository root.
- The root `README.md` is the repository entry point and links to important
  living guides and indexes.
- OMP must not scaffold or recommend OMP-owned `README.md` files in
  subdirectories.
- Non-OMP third-party/vendor or user-owned nested README files must not be
  renamed or deleted merely because they conflict with the OMP convention.

### Directory index rule

- When a directory genuinely needs an index, navigation page, catalogue or
  directory-specific instructions, name it `<folderName>Index.md`.
- The filename uses the actual folder name followed by `Index.md`.
- Do not create an index merely because a directory exists.
- Canonical OMP project-management indexes include:

  ```text
  project/requirements/requirementsIndex.md
  project/adr/adrIndex.md
  ```

- Generated links, managed documentation and readiness checks use these
  canonical paths.
- The earlier `folderIndex.md` interpretation is not canonical and must be
  treated as a recognisable migration source where OMP ownership is clear.

### Canonical requirement specifications

- Every individual requirement specification is one flat file at:

  ```text
  project/requirements/features/<nnn>-<requirementName>.md
  ```

- `<nnn>` is the permanent three-digit requirement identifier.
- `<requirementName>` is the concise camelCase requirement name.
- The identifier is allocated from
  `project/requirements/requirementsIndex.md` and is never reused.
- The specification remains at the same path throughout its lifecycle.
- Do not create a directory for an individual requirement merely to contain a
  `README.md`, index file or the specification.

### Canonical prompt files

- A requirement with one prompt uses exactly the same filename as its
  specification beneath `project/requirements/prompt/`.
- Multiple prompts use sequential lowercase suffixes on the numeric identifier
  while retaining the same requirement name.
- The unsuffixed form is used only while there is one prompt.
- If a second prompt is added later, rename the existing prompt to the `a` form,
  create `b`, and update references in the same change.
- Do not create a per-requirement prompt directory merely to contain
  `README.md`, an index file, `prompt.md` or another single prompt file.

### `manageProject --update` cleanup: directory indexes

`manageProject --update` must provide deterministic cleanup for recognised OMP
index layouts.

For requirements:

```text
project/requirements/README.md
project/requirements/folderIndex.md
    -> project/requirements/requirementsIndex.md
```

For ADRs:

```text
project/adr/README.md
project/adr/folderIndex.md
    -> project/adr/adrIndex.md
```

Rules:

- `requirementsIndex.md` and `adrIndex.md` are canonical destinations, not
  legacy names.
- Migrate only when the source content has the expected OMP index shape.
- Update actual Markdown link destinations that point to the legacy path.
- Do not rewrite historical examples or ordinary prose merely because they
  mention a legacy filename.
- If the canonical destination already exists with different meaningful
  content, preserve both and report the collision unless a no-loss resolution
  is provably safe.
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

### Scaffold and check alignment

- Newly scaffolded projects must end with
  `project/requirements/requirementsIndex.md` and `project/adr/adrIndex.md`.
- `manageProject --check` / `agentCheck` must recognise those paths as
  canonical.
- Managed documentation, generated README guidance, tests and fixtures must use
  the same convention.

## Out of scope

- Renaming or deleting third-party/vendor README files that OMP does not own.
- Renaming arbitrary user-owned README files merely to satisfy the convention.
- Creating an index in every directory regardless of need.
- Renaming valid requirement specifications or prompts solely for style.
- Combining multiple requirement specifications into one file.

## Acceptance criteria

1. Managed guidance states that `README.md` is reserved for repository root.
2. Managed guidance defines `<folderName>Index.md` as the directory-index naming
   convention when an index is needed.
3. New OMP scaffolds contain no OMP-generated nested `README.md` files.
4. New OMP scaffolds use `project/requirements/requirementsIndex.md` and
   `project/adr/adrIndex.md`.
5. Requirement specifications use
   `project/requirements/features/<nnn>-<requirementName>.md`.
6. Single prompts use
   `project/requirements/prompt/<nnn>-<requirementName>.md`, with the existing
   `a`, `b`, `c` suffix convention retained for multiple prompts.
7. `manageProject --update --confirm` safely migrates recognised requirements
   indexes from `README.md` and `folderIndex.md` to `requirementsIndex.md`.
8. The equivalent ADR migrations to `adrIndex.md` are supported.
9. Actual Markdown links to migrated indexes are updated without rewriting
   unrelated prose.
10. Dry-run reports index/artifact migrations while leaving files unchanged.
11. Existing canonical destination collisions are preserved and reported unless
    a no-loss resolution is provably safe.
12. Unrecognised/user-owned/third-party nested README files are preserved.
13. Recognisable erroneous requirement-directory and prompt-directory layouts
    are migrated to canonical flat files only when deterministic and safe.
14. Legacy directories are removed only after successful migration and only
    when empty.
15. Re-running update after successful cleanup produces no further changes.
16. `manageProject --check` recognises the named indexes and reports OMP-owned
    nested README/index mistakes.
17. Automated tests cover named-index migration, dry-run, collisions,
    user-owned README protection, requirement/prompt cleanup and idempotency.

## Dependencies and decisions

- Builds on the deterministic, ownership-safe migration policy from requirements
  001 and 003.
- Supersedes the previous OMP convention that allowed directory-specific
  `README.md` files.
- Corrects the temporary 0.6 interpretation that used literal `folderIndex.md`.
- Requirement and prompt stable-ID naming remains unchanged.

## Verification

- Review `documentation/repositoryLayout.md` and
  `documentation/requirementsManagement.md` against this requirement.
- Search OMP-managed sources for nested `README.md` and `folderIndex.md`
  assumptions.
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
- 2026-09-01: corrected to clarify the canonical numbered requirement and
  matching prompt paths.
- 2026-09-01: reserved `README.md` for repository root and added safe cleanup.
- 2026-09-01: corrected directory-index naming to `<folderName>Index.md`, making
  `requirementsIndex.md` and `adrIndex.md` canonical and `folderIndex.md` a
  migration source only.
