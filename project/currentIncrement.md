# Current Development Increment

## Increment

0.6 — Managed migration and scaffold alignment

## Status

Active

## Requirement

[004 — Requirement, prompt and directory-index layout](requirements/features/004-requirementDocumentationLayout.md)

Supporting completed work:

- [001 — Project-role-aware updates](requirements/features/001-projectRoleAwareUpdates.md)
- [003 — OMP 0.6 managed migration and project scaffold](requirements/features/003-omp06ManagedMigrationAndScaffold.md)

## Objective

Finish OMP 0.6 scaffold alignment by reserving `README.md` for the repository
root, naming directory indexes as `<folderName>Index.md`, keeping requirement
specifications/prompts as flat numbered files, and safely cleaning legacy or
mistaken OMP-generated layouts.

## Scope

- Update managed repository and requirements guidance to reserve `README.md`
  for repository root only.
- Derive OMP-managed directory index names from the containing folder when an
  index is genuinely needed.
- Use `project/requirements/requirementsIndex.md` and
  `project/adr/adrIndex.md` as the canonical project-management indexes.
- Make `manageProject --update` migrate recognised OMP-owned nested `README.md`
  and mistaken `folderIndex.md` forms to those canonical names.
- Update generated links, scaffold guidance and checks that refer to the wrong
  index paths.
- Keep requirement specifications at
  `project/requirements/features/<nnn>-<requirementName>.md`.
- Keep prompts at matching flat paths under `project/requirements/prompt/`,
  retaining the `a/b/c` suffix convention for multiple prompts.
- Extend deterministic cleanup for erroneous generated requirement/prompt
  directories containing `README.md` or equivalent recognised single files.
- Preserve ambiguous, user-owned and third-party README files.
- Cover dry-run, confirmed cleanup, collision protection and idempotent reruns.

## Explicit Exclusions

- Do not rename arbitrary user-owned or third-party README files.
- Do not create an index in every directory merely for consistency.
- Do not use the literal filename `folderIndex.md` as the canonical convention.
- Do not flatten genuine multi-file directories.
- Do not delete files or directories unless OMP can establish safe ownership
  and migration conditions.

## Verification

- [ ] Managed guidance reserves `README.md` for repository root
- [ ] Managed guidance defines `<folderName>Index.md` for directory indexes
- [ ] Requirements and ADR index migration tests
- [ ] `README.md` and mistaken `folderIndex.md` cleanup through manageProject
- [ ] Generated-link and agent-check path updates
- [ ] Requirement/prompt flat-file guidance and cleanup tests
- [ ] Dry-run migration tests
- [ ] Confirmed migration/removal tests
- [ ] Existing-destination collision protection tests
- [ ] User-owned/third-party README protection tests
- [ ] Empty-directory cleanup tests
- [ ] Idempotent rerun tests
- [ ] Full test suite
- [ ] Black and Ruff
- [ ] OMP Python and markup lint
- [ ] `python3 -m organiseMyProjects.manageProjectCli --check`

## Next

Finish scaffold/test alignment for `requirementsIndex.md` and `adrIndex.md`,
then run the full requirement 004 validation gate.
