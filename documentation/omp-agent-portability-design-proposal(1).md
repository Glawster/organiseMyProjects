# Proposal: Agent Portability in organiseMyProjects

**Scope:** Design only — no implementation. Prepared by reviewing the current
state of `Glawster/organiseMyProjects` (README, `.github/agent-instructions.md`,
`documentation/repositoryLayout.md`, `documentation/requirementsManagement.md`, and
`syncAgentInstructions.py`) before proposing anything, per the brief's
instruction to reuse existing mechanisms rather than create parallel ones.

## 0. Key finding: most of this already exists

The originating brief assumes OMP needs a vendor-neutral `AGENTS.md`, a
decisions/ADR mechanism, an OMP-owned-vs-project-owned split, and a
synchronisation system. **All four already exist**, just under different
names than the brief guessed:

| Brief asked for | Already exists as |
| --- | --- |
| Vendor-neutral `AGENTS.md` entry point | `AGENTS.md` at project root, generated from `.github/AGENTS.md`, synced by `syncAgentInstructions.py` alongside `.github/agent-instructions.md` (canonical) and `.github/copilot-instructions.md` (compatibility copy) |
| `docs/decisions/NNN-*.md` | `project/adr/NNN-camelCaseName.md`, already integrated with the requirements workflow (an ADR is linked from every requirement it supports, and vice versa) |
| `docs/requirements/` | `project/requirements/features/`, with a numbered, stable-path record format, a status index (`ToDo`/`InProgress`/`Completed`), and per-requirement agent prompts in `project/requirements/prompt/` |
| `docs/roadmap.md` | `project/roadmap.md` |
| OMP-owned vs. project-owned split | Already the organising principle of `repositoryLayout.md`: `.github/*` is synced (do-not-hand-edit, replaced on next sync), `project/` and `documentation/` are project-owned and scaffolded once |
| Sync mechanism | `syncAgentInstructions.py` — dry-run by default, `--confirm`, `--repo` (single-repo or interactive picker), `--merge` (opens and merges conflict-free PRs), version-tagged sync comments, per-repo sync branches |

So the real design problem isn't "build agent portability into OMP" — it's
**close four specific gaps** without disturbing a system that already does
most of the job, and **fold the brief's genuinely new ideas into the existing
naming, not a parallel `docs/` tree.**

Introducing `docs/architecture.md`, `docs/decisions/`, `docs/roadmap.md`, and
`docs/development/current-increment.md` as literally proposed would create a
second, competing documentation root alongside `documentation/` and `project/`
that already do this job. That's the exact failure mode
`repositoryLayout.md` warns against ("do not duplicate the same explanation in
both places"). The design below deliberately extends the existing `project/`
and `documentation/` trees instead.

## 1. The four real gaps

1. **No "current increment" record.** `project/roadmap.md` covers
   medium/long-range sequencing; nothing answers "what is actively being
   worked on right now, and what's explicitly excluded from this pass" — the
   single highest-value file for a cold-start agent, per the brief's own
   argument.
2. **No named architecture document.** `documentation/` is defined as a
   bucket for "living product, domain and contributor documentation" but no
   specific file is called out for system/component architecture the way
   `project/roadmap.md` is called out for sequencing. Nothing stops a project
   from putting architecture notes somewhere inconsistent, or nowhere.
3. **No agent-readiness validation.** Nothing today reports whether a given
   repo actually has enough of this scaffolding in place. `createProject
   --update` refreshes managed files but doesn't audit project-owned ones.
4. **AGENTS.md's actual content is unverified.** I could not fetch
   `.github/AGENTS.md` directly in this session (it isn't linked from a page
   already in context, only named in a tree diagram, and my browsing tool
   only follows links it has already seen). The README labels it "Agent
   discovery and instruction entry point," which matches the brief's intent,
   but the real content should be read before any change is scoped precisely.
   **This is the first thing to check before implementing anything below.**

## 2. Proposed design

### 2.1 `project/currentIncrement.md` (new, project-owned)

Add a fifth row to the `project/` table in `repositoryLayout.md`:

| Path | Purpose |
| --- | --- |
| `project/currentIncrement.md` | The single active unit of work: objective, in-scope behaviour, explicitly out-of-scope behaviour, and completion criteria. |

Rules, consistent with how `repositoryLayout.md` already treats
`project/roadmap.md`:

- Project-owned, scaffolded once by `createProject`, never overwritten by a
  sync.
- One file, one active increment — this is deliberately not a backlog or a
  history; superseded increments aren't archived here (that's what
  `project/reviews/` and requirement records already do). Rewriting it in
  place when an increment finishes and the next begins is expected.
- Content shape mirrors the brief's example almost exactly: `Objective`,
  `Scope`, `Explicitly Out of Scope`, `Completion Criteria`, and a link to any
  requirement(s) or ADR(s) that govern it — reusing `project/requirements/`
  and `project/adr/` rather than restating their content.
- `createProject` scaffolds an empty/starter template; the template itself
  (like `project/requirements/templates/requirement.md`) can be OMP-owned so
  its *shape* stays consistent across projects even though its *content* is
  project-owned.

### 2.2 `documentation/architecture.md` (naming convention, project-owned)

Add one row to the "Inside `documentation/`" guidance (currently
`repositoryLayout.md` only tabulates `project/`, not `documentation/`) naming
`documentation/architecture.md` as the conventional home for "how the system
is designed" — components, data flow, key dependencies, and why the shape is
what it is at a whole-system level (as distinct from an ADR, which explains
one consequential decision). This is a documentation convention, not new
tooling: it just gives `omp validate` (below) and `AGENTS.md` something
specific to point to instead of "read `documentation/`."

### 2.3 `omp validate` (new CLI command, OMP-owned tooling)

A new subcommand, consistent with the CLI standards already defined in
`agent-instructions.md` (`application object action`, `--confirm`/`--verbose`
universal options, non-interactive by default, exit code 0/non-zero):

```bash
omp validate
omp validate --repo <path>      # defaults to CWD
omp validate --verbose
```

Checks presence (not content quality) of:

- `AGENTS.md`, `README.md` (with a Documentation section, per existing
  `repositoryLayout.md` rule)
- `documentation/architecture.md`
- `project/roadmap.md`
- `project/requirements/` (README + at least the index)
- `project/currentIncrement.md`
- `project/adr/` (presence, not that it's non-empty — not every project needs
  a decision record yet)
- `.github/agent-instructions.md`, `.github/copilot-instructions.md`,
  `documentation/repositoryLayout.md`, `documentation/requirementsManagement.md` (i.e.
  synced files are actually present and carry the sync comment)
- Test and coding-standard entry points referenced from
  `agent-instructions.md` are resolvable (e.g. a `tests/` directory exists)

Output format matches the brief's sketch (✓/✗ list ending in a summary
verdict). This is presence/structure validation only — a second, harder
command (`omp agent-check`, staleness detection) is worth naming as a future
phase but is out of scope for a first implementation; it needs a strategy for
comparing doc freshness against commit history that deserves its own design
pass rather than being bundled in here.

### 2.4 Sync-list changes

Add to `SYNC_SPECS` in `syncAgentInstructions.py`:

- The `project/currentIncrement.md` **template** would *not* be added here —
  templates for project-owned files should be delivered by
  `createProject`/`createProject --update` (create-if-missing), not by the
  sync script (which is specifically for files that get overwritten in
  place). Mixing the two would blur exactly the distinction
  `repositoryLayout.md` exists to protect.
- No change needed to sync `documentation/architecture.md` for the same
  reason — it's a convention `createProject` seeds once, not a managed file.

## 3. Files added or modified

**Modified (OMP-owned, edited once in `organiseMyProjects`, then synced):**

- `documentation/repositoryLayout.md` — add `project/currentIncrement.md` row;
  add a documentation-conventions row naming `documentation/architecture.md`.
- `.github/agent-instructions.md` — reference `project/currentIncrement.md`
  and `documentation/architecture.md` in whichever section currently tells an
  agent what to read first (needs the unread `AGENTS.md`/entry-point content
  to place this precisely).
- `.github/AGENTS.md` — same, once its current content is confirmed.

**New (OMP-owned):**

- `omp validate` command implementation, wherever `createProject`'s CLI is
  defined (needs `createProject.py`/CLI entry-point layout confirmed before
  scoping the exact module).
- `project/currentIncrement.md` template, distributed the same way
  `project/requirements/templates/requirement.md` already is.

**New (project-owned, created once by `createProject`, never resynced):**

- `project/currentIncrement.md` (starter content) in every newly scaffolded
  project.
- `documentation/architecture.md` (starter stub) in every newly scaffolded
  project.

**Not changed:** `project/adr/`, `project/requirements/`,
`project/roadmap.md`, the OMP/project-owned split itself, and the sync
script's PR/branch mechanics — all already do what the brief asked for.

## 4. Migration implications for existing OMP-managed repos

- **Zero disruption to already-synced files.** The four existing
  `SYNC_SPECS` entries are unaffected; existing repos keep working exactly as
  they do today until they're next synced.
- **`project/currentIncrement.md` and `documentation/architecture.md` are
  new project-owned files.** They can't be pushed via the sync script
  (that would violate the project-owned boundary). They'd be added the same
  way any other project-owned scaffold gap is closed today: `createProject
  <name> --update`, which "replace[s] missing scaffold files" while leaving
  existing project-owned content untouched. That already-documented behaviour
  is exactly the right mechanism — no new update path is needed.
- **`omp validate` run against an existing repo will initially report gaps**
  for every repo created before this change (missing `currentIncrement.md`,
  missing `documentation/architecture.md`). That's expected and is the
  intended signal for maintainers to run `createProject --update` on each one
  — not something `omp validate` should try to silently fix.
- **No renames, no data loss.** Nothing existing moves paths; this is
  additive only.

## 5. Before implementing: three things to verify

1. Read the actual current content of `.github/AGENTS.md` (I could not reach
   it from this session — it wasn't linked from anywhere already fetched).
   Confirm it's already the thin navigation pointer the brief wants; if it's
   heavier, that's a separate, larger change than anything above.
2. Read `createProject.py` to confirm where "create scaffold file if missing"
   logic lives, so the two new project-owned templates plug into the existing
   mechanism instead of a new one.
3. Confirm whether `documentation/` currently has any per-directory
   convention table in `repositoryLayout.md` (it currently only tabulates
   `project/` in detail) — if not, adding one row for `architecture.md` is a
   small, low-risk addition; if `documentation/` conventions live elsewhere,
   the edit target changes.

## 6. On testing this with Claude vs. Gemini

The brief's own suggestion — running this same review-and-propose task
independently through Claude Code and Gemini CLI against a branch of the
real repo — is worth doing regardless of this document. It would catch
exactly the kind of thing this proposal surfaced: an outside brief describing
a `docs/` tree that would have silently duplicated a `project/`/`documentation/`
split that already exists. A cold-start agent without repo access (as I was,
partially, in this session) can only reason from what it's shown; one with
full repo access should independently arrive at "extend `project/`, don't
invent `docs/`" — and if it doesn't, that's itself useful evidence about how
well `repositoryLayout.md` currently orients a new agent.
