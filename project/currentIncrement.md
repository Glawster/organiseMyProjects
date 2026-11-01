# Current Development Increment

## Increment

0.10a2 — Agent account availability and resume approval options

## Status

InReview

## Objective

Deliver [028: Agent usage availability](requirements/features/028-agentUsage.md)
on `release/0.10`, including explicit permission policies for session resumption.

## Implementation

- `agentSessions --usage` queries every supported provider independently and
  renders account capacity remaining, with separate windows and local reset times.
- `agentUsage.py` owns provider acquisition, explicit percentage conversion,
  normalisation, safe statuses and table formatting. `claudeUsage.py` adds the
  user-approved terminal fallback using the `pyte` runtime dependency.
- Presentation uses aligned agent/window/available/reset columns, one quota per
  line and a blank line between agents; redundant default bucket names are omitted.
- Protocol calls use bounded subprocesses; tests verify timeout cleanup. No
  model turns, session token totals, direct credential-file reads or raw response
  logging are used to obtain capacity.
- Session-specific flags conflict with `--usage`; help, quiet and verbose work.
- The maintained agent sessions guide documents interface provenance, semantics,
  authentication states and known limitations.

## Copilot presentation correction

- A live account read confirmed exhausted premium interactions alongside unlimited
  chat/completions, which the provider represents as 100% remaining.
- Premium interactions now appear first; unlimited entitlements render as
  `UNLIMITED`. Finite remaining percentages retain their original meaning.
- Focused provider/session/Claude regression suite: 120 passed, including CLI
  protocol coverage of exhausted premium and unlimited base services. Black,
  Ruff and diff whitespace checks pass.
- Scope remains OMPR only; OMS, OMV and OMP have no runtime impact.

## Resume approval options

- Resume commands add Codex `--ask-for-approval never`, Claude
  `--permission-mode auto`, Grok `--permission-mode dontAsk`, and Copilot
  `--allow-all-tools`. Claude uses `auto` at the user's request.
- CLI help and manual resume examples document the same flags and semantics.
- Existing resume regression verifies command construction and terminal handoff.
- Scope remains OMPR only; OMS, OMV and OMP have no runtime impact.

## Verification

- Full suite: 627 passed with no skips in the `ompr` environment; focused
  provider/session/Claude terminal suite: 120 passed.
- Version `0.10a2` and release notes cover quota presentation and resume approval
  options. Repository source lint (66 files), markup lint, Black, Ruff and diff
  whitespace validation pass.
- Synthetic CLI subprocesses exercise Codex/Grok line-based JSON-RPC and Copilot
  Content-Length framing, with independently specified quota expectations.
- Tests cover used/remaining conversion, boundaries, malformed/missing fields,
  named buckets, multiple windows, resets, auth errors, isolation and timeouts.
- Claude tests cover screenshot-derived quota expectations, additional weekly
  bars, malformed/partial screens, real terminal redraws, timezone/date rollover,
  startup dialog rejection and reaping stalled processes.
- Existing session listing, search, filters, history and resume regressions pass.
- Black, Ruff, targeted OMP source lint, repository markup and diff whitespace
  validation pass.
- Isolated source distribution and wheel builds pass; the wheel includes the
  Claude adapter and declares the `pyte` dependency.
- Repository readiness check: zero failures, six existing requirement-template
  warnings in unrelated requirements.
- Live read-only verification: Codex and Copilot return account quota percentages;
  Grok returns the billing period but omits `creditUsagePercent`; Claude Code
  2.1.314 `/usage` capture returns session/weekly percentages and timezone resets.

## Limitations and review

- Claude terminal scraping is less stable than an account protocol. It uses a
  separate safe-mode process, rejects dialogs, preserves redraw semantics and
  falls back to `UNKNOWN` on unsupported platforms or changed/ambiguous screens.
  No direct OAuth extraction or undocumented endpoint was introduced.
- Grok 1.0.70 reports `weekly: UNKNOWN` alongside its supplied reset when the
  percentage is missing. Financial counts are deliberately not converted.
- Independent review and human acceptance remain before merge.
- This is an OMPR developer command. OMS, OMV and OMP have no code/runtime impact.

## Backlog retained for 0.10

- [002: Runtime infrastructure synchronisation](requirements/features/002-runtimeInfrastructureSync.md): runtime-sharing ADR and reserved package-name decision.
- [024: Requirement board branch versions](requirements/features/024-myBoardBranchVersions.md): unmerged local and remote branches with their versions.
