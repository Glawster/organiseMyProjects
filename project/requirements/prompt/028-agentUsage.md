# 028: Agent usage availability

## Assignment

Implement and verify [requirement 028](../features/028-agentUsage.md) following the repository `.github` guidance and existing `agentSessions` conventions.

Add `agentSessions --usage` without regressing the existing session listing/resume command. The feature must query Claude, Codex, Grok and Copilot independently, preserve provider-specific quota windows, and normalise every reported percentage to **percentage available/remaining**.

## Required approach

1. Inspect the installed/current provider interfaces before choosing an acquisition mechanism. Prefer supported CLI, SDK, ACP/app-server or other machine-readable interfaces over terminal-screen scraping.
2. Keep each provider behind a small adapter with a common normalised result type. Provider acquisition/parsing must remain separate from table rendering.
3. Explicitly record whether each provider field is `used` or `remaining`; never guess from an unlabeled number.
4. Convert used values using `100 - used`; use remaining values directly; clamp final percentages to 0–100.
5. Preserve independently binding windows. Do not average short-term and weekly availability into one number.
6. Treat inability to obtain account-wide quota as `UNKNOWN`. Do not substitute per-session token/credit statistics.
7. Do not log or print access tokens, refresh tokens, credential file contents or authorization headers. Avoid direct credential handling where a provider protocol can obtain quota on the user's behalf.
8. Provider failures must be isolated so one unavailable CLI/account still allows the other rows to render.

## Provider investigation targets

- **Claude:** Claude Code exposes five-hour and seven-day rate-limit utilisation. Prefer a supported Claude Code interface/control surface. If the only possible mechanism requires direct OAuth-token extraction or an undocumented endpoint, do not silently add that dependency: keep the adapter `UNKNOWN` and document the limitation unless the repository/user explicitly approves that approach.
- **Codex:** investigate the current Codex account-rate-limit interface/app-server. Its rate-limit snapshots expose `used_percent`, window duration and reset time. Convert to remaining percentage.
- **Grok:** investigate the current Grok Build billing/usage interface (including its supported agent/ACP extension surface) for the shared weekly usage pool. Convert provider-native percentage used to remaining percentage. Do not use the per-session token/cost `usage` command as account availability.
- **Copilot:** use the supported Copilot account quota interface where available. `account.getQuota`/quota snapshots expose `remainingPercentage` and reset date. Do not use `/usage` session token totals as account availability.

## Output

Keep the output compact and terminal friendly. A suitable shape is:

```text
AGENT    SHORT AVAILABLE   SHORT RESET   WEEKLY AVAILABLE   WEEKLY RESET
Claude   63%               22:14         81%                Mon 09:00
Codex    74%               23:05         58%                Sun 18:00
Grok     —                 —             46%                Mon 00:00
Copilot  82%               23:40         67%                Fri 16:00
```

Use provider-appropriate window names if the returned quota model differs. `UNKNOWN`, `NOT INSTALLED` and `NOT AUTHENTICATED` must remain distinguishable from `0%`.

## Verification

Add focused tests for adapter parsing and normalisation, provider failure isolation and rendering. Run the existing `agentSessions` tests as regression coverage plus the repository's normal test/lint commands. If a provider requires an installed/authenticated external CLI for integration testing, keep unit tests deterministic with captured representative protocol responses and report any manual verification separately.

Do not commit secrets, captured auth files or bearer tokens in fixtures.

## Approved Claude fallback

The user approved terminal scraping of Claude Code's built-in `/usage` on
2026-10-30. Use a separate safe-mode POSIX terminal and interpret its rendered
state with `pyte`; do not scrape browser pages or extract OAuth tokens. Submit
only `/usage`, reject startup/trust/login dialogs, preserve all quota windows,
and terminate the process group on success, failure and timeout. Do not save or
log screen contents. Keep `UNKNOWN` when the UI cannot be read confidently.
