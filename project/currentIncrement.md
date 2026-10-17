# Current Development Increment

## Increment

0.8 — Repository root awareness and shared TUI buttons

## Status

ReleaseReady — OMP 0.8 scope verified; outstanding acceptance work carries into 0.9.

## Requirements

- [011: Repository and project root awareness](requirements/features/011-repositoryAndProjectRootAwareness.md) — Completed.
- [012: Shared TUI button presentation](requirements/features/012-sharedTuiButtonPresentation.md) — InProgress.

## Delivered work

- Git-aware repository-root discovery for repository-owned entry points and
  verification guidance, with deterministic non-Git/missing-Git fallback.
- Project checks retain the selected project root; diagnostics show both roots
  when they differ or verbose output is requested.
- Shared one-row Textual buttons with clipping-safe borders/padding across
  interaction states, semantic colours and opt-in equally sized horizontal groups.
- Shared-theme creation/update deployment with CSS provenance, dry-run and
  idempotency; custom themes are preserved and `clannEolas` is exempt.
- Canonical TUI adoption guide and development-only Textual dependency.

## Verification

- Full pytest suite: 420 passed using the existing mailAgent Conda environment.
- Regression coverage includes a real nested-project CLI check, genuine missing
  repository entry points, project-local test settings and Git discovery fallback.
- Real Textual rendering verified at 81×24, 80×24, 41×16 and 40×16; widths differ
  by at most one column when fractional sizes require integer rounding.
- Release checks pass pytest, Black, Ruff, OMP source/markup lint and
  `manageProject check`; source distribution and wheel builds succeed.
- Repository-wide markup validation passes after correcting duplicate headings,
  prompt titles and excess blank lines.
- Source distribution and wheel build successfully; wheel stylesheet and source
  distribution guide match the canonical files.

## Remaining work and decisions

- Requirement 012 acceptance criterion 6 requires adoption in `mailAgent` and
  removal of execution-screen-specific button height/border overrides. That
  checkout is not available locally, so downstream rendering is unverified.
- Requirement 002 remains pending because its copied `omp` runtime package and
  imports conflict with the authoritative instructions and superseded ADR-002.
  Resolve that requirement before implementing runtime synchronisation.
- Requirement 004 already has migration/check implementations and passing
  regression tests; its existing InProgress status is retained for acceptance review.
- Release closure uses a squash pull request into `main`, an annotated `v0.8`
  tag and a new `release/0.9` development branch.
- Suite impact: OMS, OMV and OMP may opt into shared Textual styling; their existing
  Qt/Tkinter UIs require no changes. OMPR owns theme and check implementation.
