# Current Development Increment

## Increment

0.10 — Agent account availability

## Status

InReview

## Objective

Deliver [028: Agent usage availability](requirements/features/028-agentUsage.md)
on `feature/028-agent-usage` without changing session listing or resumption.

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

## Verification

- Full suite: 625 passed with no skips in the `ompr` environment; focused
  provider/session/Claude terminal suite: 118 passed.
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
