# AI Agent Portability and Context Integrity Design (Revised)

## Table of Contents

1. [Minimum Viable First Increment](#1-minimum-viable-first-increment)
2. [Existing OMP Mechanisms: Reuse vs Additions](#2-existing-omp-mechanisms-reuse-vs-additions)
3. [File-Level Inventory and Ownership Matrix](#3-file-level-inventory-and-ownership-matrix)
4. [Strengthened Current Development Record (`project/currentIncrement.md`)](#4-strengthened-current-development-record-projectcurrentincrementmd)
5. [Vendor Shim Strategy & Justification](#5-vendor-shim-strategy--justification)
6. [Agent-Readiness Validation Engine (`agentCheck`)](#6-agent-readiness-validation-engine-agentcheck)
7. [Non-Destructive Migration for Existing Repositories](#7-non-destructive-migration-for-existing-repositories)
8. [Explicitly Deferred Future Enhancements](#8-explicitly-deferred-future-enhancements)
9. [Pre-Implementation Assumptions & Verifications](#9-pre-implementation-assumptions--verifications)
10. [End-to-End Acceptance Test](#10-end-to-end-acceptance-test)

---

## 1. Minimum Viable First Increment

### 1.1 Objective

To enable an AI coding agent with **zero prior conversation history** to open an OMP-managed repository and independently determine:

1. The project's purpose and system context.
2. Architecture boundaries and build/run/test procedures.
3. The exact objective, scope, and exclusions of the **current development increment**.
4. The governing requirements and architectural decision records (ADRs).
5. Universal coding, logging, testing, and release standards.
6. The sensible next action for implementation or verification.

```text
                                AGENTS.md
                       (Canonical Agent Discovery)
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌────────────────────────────────┐         ┌─────────────────────────────────┐
│      OMP-Owned Standards       │         │     Project-Owned Knowledge     │
│   (Synchronised by OMP v0.4)   │         │     (Scaffolded, Never Synced)  │
├────────────────────────────────┤         ├─────────────────────────────────┤
│ .github/agent-instructions.md  │         │ README.md (Overview & Doc Index)│
│ documentation/repositoryLayout │         │ documentation/architecture.md   │
│ documentation/requirements... │         │ project/roadmap.md              │
│ documentation/howToRelease.md │         │ project/requirements/           │
│ Vendor Shims (Copilot, Claude) │         │ project/adr/                    │
│ tests/agentCheck.py (Linter)   │         │ project/currentIncrement.md     │
└────────────────────────────────┘         └─────────────────────────────────┘
                                   ▲
                                   │ validates
                    ┌──────────────┴──────────────┐
                    │          agentCheck         │
                    │   (Deterministic Validator) │
                    └─────────────────────────────┘
```

### 1.2 Scope Boundaries for Increment 1

- **In Scope**:
  - `AGENTS.md` as universal discovery root with lightweight, justified vendor shims.
  - Standardized project-owned documentation templates: `documentation/architecture.md`, `project/currentIncrement.md`, `project/roadmap.md`, `project/project.yaml`, `project/requirements/templates/requirement.md`, `project/adr/templates/adr.md`.
  - Non-destructive scaffolding via `createProject` and `updateProject` (strictly preserving existing project-owned files).
  - Deterministic structural and relational validation tool (`agentCheck`) checking cross-references, status agreements, and unconfigured placeholders.
  - Elimination of the 22KB duplicate `copilot-instructions.md` in favor of a 3-line pointer shim.
- **Explicitly Out of Scope**:
  - Unified CLI framework rewrite (e.g. `omp` subparser umbrella).
  - GitHub Projects / Kanban / issue-tracker integration.
  - Multi-project portfolio orchestration.
  - AI-driven or heuristic prose quality evaluation.

---

## 2. Existing OMP Mechanisms: Reuse vs Additions

OMP already has proven scaffolding, synchronization, and code quality tools. We extend them directly rather than creating parallel systems:

| Capability Needed | Existing OMP Mechanism | Planned Reuse / Extension | Rationale / Minimal Change |
| :--- | :--- | :--- | :--- |
| **Remote Standards Sync** | `syncAgentInstructions.py` | **Reuse with minor spec update** | Update `SYNC_SPECS` to sync lightweight pointer shims (`CLAUDE.md`, `.github/copilot-instructions.md`) instead of duplicate full instruction bodies. Maintain GitHub API, PR creation, and token storage. |
| **Local Project Scaffolding** | `organiseMyProjects/manageProject.py` | **Extend `PROJECT_TEXT_TEMPLATES`** | Add missing project-owned templates (`currentIncrement.md`, `architecture.md`, `roadmap.md`, `project.yaml`, ADR/requirement templates). These are written *only if missing* and never overwritten during `--update`. |
| **Logging & Output** | `organiseMyProjects/logUtils.py` / `.sh` | **Reuse directly** | Use standard semantic methods (`doing`, `done`, `info`, `value`, `action`) for the `agentCheck` utility. |
| **Code / Layout Linting** | `guiNamingLinter.py` / `runLinter.py` | **Reuse pattern** | Follow the established linter pattern (dual-purpose utility in package + test entry point) for the new `agentCheck.py` tool. |
| **Repository Layout Definition** | `documentation/repositoryLayout.md` | **Extend tables in place** | Formalize `project/currentIncrement.md` and `documentation/architecture.md` inside the existing layout tables. |
| **Requirements Management** | `documentation/requirementsManagement.md` | **Reuse directly** | The existing 3-digit requirement workflow (`features/`, `prompt/`, `README.md` matrix) is already robust and remains unchanged. |
| **Release Workflow** | `documentation/howToRelease.md` | **Reuse directly** | Standard `vX.Y` tagging and `release/X.Y` branch workflow remains authoritative. |

---

## 3. File-Level Inventory and Ownership Matrix

Every artifact touched or introduced by OMP is strictly classified under one ownership category:

### 3.1 OMP-Owned Standards & Tools (Synchronised & Managed)

*Managed by OMP; overwritten or synchronized via PR during updates/releases.*

| Path | Purpose | Lifecycle & Sync Behavior |
| :--- | :--- | :--- |
| `AGENTS.md` | Canonical discovery entry point for all agents | Synced from OMP template; includes release comment header. |
| `.github/agent-instructions.md` | Universal master guidelines (v2) | Synced from OMP template; single source of truth for coding/testing/logging rules. |
| `.github/copilot-instructions.md` | GitHub Copilot discovery shim | Synced pointer shim directing Copilot to `AGENTS.md`. |
| `CLAUDE.md` | Claude Code discovery shim | Synced pointer shim directing Claude Code to `AGENTS.md`. |
| `documentation/repositoryLayout.md` | Authoritative directory placement rules | Synced from OMP template. |
| `documentation/requirementsManagement.md` | Canonical requirements workflow | Synced from OMP template. |
| `documentation/howToRelease.md` | Release and tag governance | Synced from OMP template. |
| `organiseMyProjects/agentCheck.py` | Package module for validation | Maintained in OMP package. |
| `tests/agentCheck.py` | Local test entry point for validation | Scaffolded/synced into `tests/` across managed projects. |

### 3.2 Project-Owned Knowledge & Governance (Scaffolded Once, NEVER Overwritten)

*Scaffolded as initial templates on creation/update if missing; owned exclusively by the project thereafter.*

| Path | Purpose | Lifecycle & Guard Policy |
| :--- | :--- | :--- |
| `README.md` | Human/agent project overview & doc index | Created once with `# {projectName}` and `## Documentation` index. Never overwritten. |
| `.github/additional-instructions.md` | Project-specific constraints and run commands | Created once with project defaults. Never overwritten. |
| `project/currentIncrement.md` | Active increment goal, tasks, and state | Scaffolded once from template if missing. Never touched by OMP sync. |
| `project/project.yaml` | Structured metadata (purpose, runtime, role) | Scaffolded once from template if missing. Never touched by OMP sync. |
| `project/roadmap.md` | Milestone sequencing and priorities | Scaffolded once from template if missing. Never touched by OMP sync. |
| `project/requirements/` | Requirements index, features, and prompts | Scaffolded once with templates (`requirement.md`, `README.md`). Never overwritten. |
| `project/adr/` | Architectural Decision Records | Scaffolded once with templates (`adr.md`, `README.md`). Never overwritten. |
| `project/reviews/` | Point-in-time assessment records | Scaffolded directory. Never overwritten. |
| `documentation/architecture.md` | Living component boundaries and data flow | Scaffolded once from template if missing. Never touched by OMP sync. |
| `documentation/developer.md` | Contributor and environment guide | Scaffolded once from template if missing. Never touched by OMP sync. |

---

## 4. Strengthened Current Development Record (`project/currentIncrement.md`)

### 4.1 Placement Decision

Following `documentation/repositoryLayout.md`, top-level operational files in `project/` live directly under `project/` alongside `project/project.yaml` and `project/roadmap.md`, while historical/domain subtrees use dedicated directories (`requirements/`, `adr/`, `reviews/`).

Therefore, the active state file is **`project/currentIncrement.md`**.

### 4.2 Template Specification

The template is the sole transient implementation-status record. It stays small
enough to replace when the active increment changes instead of accumulating a
delivery history:

```markdown
# Current Development Increment

## Increment

001A — Feature name

## Status

Active
<!-- Options: Active, Idle, Blocked, InReview -->

## Requirement

`project/requirements/features/001-featureName.md`

## Objective

<!-- Short statement of what capability is being delivered right now. -->

## Scope

- Behaviour included in this increment.

## Verification

- [ ] Focused tests
- [ ] Full suite
- [ ] Manual acceptance

## Next

<!-- Immediate next action or known next increment. -->
```

Requirements retain lifecycle states such as `ToDo`, `InProgress` and
`Completed`, while this file owns the changing task and verification detail.
ADRs own decisions, living documentation owns durable behaviour, tests own
executable evidence and Git owns delivery history.

---

## 5. Vendor Shim Strategy & Justification

To maintain vendor neutrality while accommodating tool-specific discovery conventions, lightweight shims are used only where hardcoded discovery paths exist:

| File | Target Tool | Discovery Mechanism Justification | Content |
| :--- | :--- | :--- | :--- |
| `AGENTS.md` | Universal Standard / Linux Foundation / Codex / Antigravity | Root-level discovery standard for multi-agent repositories. | Direct pointer referencing `.github/agent-instructions.md` and optional `.github/additional-instructions.md`; the canonical instructions load the other mandatory guides. |
| `.github/copilot-instructions.md` | GitHub Copilot | GitHub Copilot specifically looks for `.github/copilot-instructions.md` in repository settings and web context. | **Direct Shim**: Replaces the old 22KB duplicate with a direct pointer to `.github/agent-instructions.md` and `.github/additional-instructions.md`. |
| `CLAUDE.md` | Claude Code | Claude Code automatically reads `CLAUDE.md` from the project root at session initialization. | **Direct Shim**: Direct pointer to `.github/agent-instructions.md` and `.github/additional-instructions.md`. |
| *Others (Cursor, Gemini CLI, Roo, etc.)* | Native / Workspace | These tools natively parse `AGENTS.md` or workspace root files; no additional shims required. | *None required.* |

### Standard Shim Content (`.github/copilot-instructions.md` and `CLAUDE.md`)

```markdown
<!-- deployed from Glawster/organiseMyProjects release 0.4 -- do not edit directly -->
# Agent Instructions

Read and follow `.github/agent-instructions.md`.

Also read and follow `.github/additional-instructions.md` when it exists.
```

---

## 6. Agent-Readiness Validation Engine (`agentCheck`)

`agentCheck` is a deterministic static analyzer. It evaluates repository consistency, relational integrity, and placeholder elimination.

### 6.1 Invocation & Interface

```bash
# Direct test entry point in project
python tests/agentCheck.py

# Via package entry point
python -m organiseMyProjects.agentCheck

# Optional strict mode for CI (warnings fail the run)
python tests/agentCheck.py --strict
```

### 6.2 Relational Validation Engine

```text
                                agentCheck
                                    │
    ┌───────────────────┬───────────┴───────────┬───────────────────┐
    ▼                   ▼                       ▼                   ▼
1. Entry Points     2. Living Docs & Build  3. Current Increment    4. Requirements & ADRs
- AGENTS.md exists  - README links docs     - Requirement exists    - Req index matches
- Shims point to    - Build/run commands      and is not Completed    features/ files
  AGENTS.md           in additional-        - Files in increment    - Matrix status ==
- Additional-         instructions.md         exist on disk           file status
  instructions ok   - Zero dead links       - No scaffold template  - ADR links resolve
                                              placeholders left     - Completed work has
                                                                      test evidence
```

### 6.3 Rule Definitions and Severity Levels

| Rule ID | Level | Check Description | Failure Condition |
| :--- | :--- | :--- | :--- |
| **`ENT-001`** | **FAILURE** | Agent Entry Point | `AGENTS.md` missing or does not link to `.github/agent-instructions.md`. |
| **`ENT-002`** | **WARNING** | Vendor Shims | `CLAUDE.md` or `.github/copilot-instructions.md` missing or contains divergent text instead of standard pointer shim. |
| **`DOC-001`** | **FAILURE** | Documentation Index | `README.md` missing `## Documentation` section or does not link to living files under `documentation/`. |
| **`DOC-002`** | **FAILURE** | Link Integrity | Internal Markdown link points to a non-existent file or anchor. |
| **`DOC-003`** | **FAILURE** | Build/Test Procedures | `.github/additional-instructions.md` does not specify verification commands. |
| **`INC-001`** | **FAILURE** | Current Increment Exists | `project/currentIncrement.md` is missing. |
| **`INC-002`** | **FAILURE** | Increment Consistency | `currentIncrement.md` is `Active` but references a requirement marked `Completed` or not found in `project/requirements/features/`. |
| **`INC-003`** | **WARNING** | Increment File Resolution | A path listed under the legacy `Relevant Files & Components` heading does not exist on disk. Retained for compatibility with existing project-owned increment files. |
| **`INC-004`** | **WARNING** | Placeholder Detection | `currentIncrement.md` contains unedited scaffold placeholders (e.g. `<!-- Concise 1-2 sentence... -->` or `Deliverable behavior 1`). |
| **`REQ-001`** | **FAILURE** | Requirements Index Alignment | A file exists in `project/requirements/features/` but is missing from `project/requirements/README.md` (or vice versa). |
| **`REQ-002`** | **FAILURE** | Status Agreement | The `Status` column in `project/requirements/README.md` contradicts the `## Status` in the feature file. |
| **`REQ-003`** | **FAILURE** | ADR Reference Integrity | An ADR linked in a requirement or current increment does not exist in `project/adr/`. |

*Note: No rule checks document age or timestamps. Staleness is evaluated strictly through concrete structural contradictions.*

---

## 7. Non-Destructive Migration for Existing Repositories

For existing repositories (e.g., `fmsat`, `sportVision`, `eolas`):

```text
Step 1: Release OMP v0.4
   │
Step 2: Remote Standards Sync (python syncAgentInstructions.py --confirm --merge)
   ├── Updates AGENTS.md, .github/agent-instructions.md, documentation/repositoryLayout.md
   └── Deploys lightweight shims (CLAUDE.md, copilot-instructions.md)
   │
Step 3: Local Scaffolding Update (createProject --update)
   ├── Installs tests/agentCheck.py
   └── Scaffolds missing project/currentIncrement.md and documentation/architecture.md
       (Existing README.md, additional-instructions.md, and features are UNTOUCHED)
   │
Step 4: Verification (python tests/agentCheck.py)
   └── Run check locally to confirm repository passes all consistency checks
```

1. **Safety Guarantee**: `syncAgentInstructions.py` operates solely on `SYNC_SPECS` (`.github/` standards, `AGENTS.md`, and vendor shims). It never reads, modifies, or deletes project-owned folders.
2. **Idempotence**: Running `createProject --update` multiple times will never overwrite customized files.

---

## 8. Explicitly Deferred Future Enhancements

The following capabilities are deliberately excluded from Increment 1:

1. **Unified `omp` CLI Dispatcher**: Consolidating `createProject`, `runLinter`, and `agentCheck` into an `omp <subcommand>` CLI. *(Reason: Existing standalone entry points work; changing CLI structure increases migration churn without improving agent portability).*
2. **GitHub Projects / Issue Tracker Sync**: Automated two-way sync between `project/currentIncrement.md` and GitHub Issues / Project Boards. *(Reason: Repository-local files must be the source of truth; external sync is a separate feature).*
3. **Multi-Project Portfolio Overview**: Aggregated status reporting across multi-repository workspaces. *(Reason: Increment 1 focuses on individual repository autonomy).*
4. **AI-Assisted Documentation Evaluation**: Using LLM calls to critique documentation clarity or tone. *(Reason: Validation must remain deterministic, fast, offline, and zero-cost in CI).*

---

## 9. Pre-Implementation Assumptions & Verifications

Before implementing Increment 1, verify the following in the repository:

1. **GitHub Copilot Token Permissions**: Confirm that GitHub PATs used by `syncAgentInstructions.py` have sufficient `repo` permissions to create branches and pull requests for new shim paths (`CLAUDE.md`).
2. **Pre-commit Compatibility**: Ensure adding `tests/agentCheck.py` as a pre-commit check does not cause circular dependencies or performance regressions in local git hooks.
3. **Conda / Virtualenv Packaging**: Confirm `organiseMyProjects` editable installs (`pip install -e .`) correctly expose `organiseMyProjects.agentCheck` across consuming environments.

---

## 10. End-to-End Acceptance Test

### Test Scenario: "Zero-History Agent Bootstrap"

**Context**: A fresh AI coding agent is initialized in an OMP-managed repository with **no previous conversation history or chat context**.

#### Step 1: Bootstrap Execution

The agent is prompted:
> *"Inspect this repository and summarize the active work state and standards."*

#### Step 2: Observable Agent Actions

1. The agent reads `AGENTS.md` (or discovers it via `CLAUDE.md` / `.github/copilot-instructions.md`).
2. The agent follows the shim to `.github/agent-instructions.md`, which requires `documentation/requirementsManagement.md`, `documentation/repositoryLayout.md`, and `documentation/testingProcess.md`, and reads optional `.github/additional-instructions.md`.
3. The agent navigates to `project/currentIncrement.md` and reads the linked requirement in `project/requirements/features/` and architecture in `documentation/architecture.md`.

#### Step 3: Acceptance Assertions

The test passes if and only if the agent's response accurately states:

- [x] **Project Purpose**: Correct summary of what the project does from `README.md` and `project/project.yaml`.
- [x] **Architecture Boundaries**: Explicit mention that core domain logic has no UI dependencies and UI modules only orchestrate.
- [x] **Active Objective**: Exact statement of what is currently being delivered in `project/currentIncrement.md`.
- [x] **Governing Requirements & ADRs**: Accurate links to the active requirement ID and any related ADRs.
- [x] **Explicit Exclusions**: Accurate list of excluded scope from `project/currentIncrement.md`.
- [x] **Verification Commands**: Exact test and lint commands from `currentIncrement.md` and `.github/additional-instructions.md`.
- [x] **Sensible Next Action**: Concrete identification of the next in-progress task from `project/currentIncrement.md` ready for implementation.
- [x] **Verification Gate**: Execution of `python tests/agentCheck.py` exits with status code `0`.
