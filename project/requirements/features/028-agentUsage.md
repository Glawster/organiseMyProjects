# 028: Agent usage availability

## Status

InProgress

## Requirement

As a developer using several AI coding agents, I need `agentSessions --usage` to show how much usable plan capacity remains for Claude, Codex, Grok and Copilot in one common format, so that I can choose an agent that has enough availability for the next piece of work.

The command shall normalise every provider to **percentage available/remaining**. Provider-native percentages reported as used/consumed shall be converted with `100 - used`. Raw token, credit or request counts are not useful as the primary comparison and shall not be substituted for a percentage when a trustworthy percentage cannot be calculated.

## Behaviour

`agentSessions --usage` shall report one row per supported agent. Where an agent has more than one independently binding allowance, the command shall show the relevant windows separately rather than collapsing them into a misleading single number. Reset times shall be shown when the provider supplies them.

The preferred presentation is compact and comparable, for example:

```text
AGENT    SHORT AVAILABLE   SHORT RESET   WEEKLY AVAILABLE   WEEKLY RESET
Claude   63%               22:14         81%                Mon 09:00
Codex    74%               23:05         58%                Sun 18:00
Grok     —                 —             46%                Mon 00:00
Copilot  82%               23:40         67%                Fri 16:00
```

The exact window labels may differ when a provider exposes different quota types, but every percentage displayed by this command shall mean capacity remaining.

If a provider is installed but its current allowance cannot be read reliably, report `UNKNOWN` for that value. Do not infer availability from session token counts, AI-credit totals, historic usage, configured plan limits or undocumented assumptions.

If a provider is not installed or not authenticated, distinguish that from an exhausted allowance.

## Provider notes

- Claude exposes five-hour and seven-day rate-limit utilisation in Claude Code. Values are provider-native usage percentages and therefore need conversion to remaining percentage. The implementation should prefer a supported Claude Code interface and must not expose or log OAuth credentials.
- Codex exposes primary and secondary account rate-limit windows including `used_percent` and reset timestamps. Convert those values to remaining percentage.
- Grok uses a shared weekly usage pool reported as percentage used. Convert that value to remaining percentage. Prefer the supported Grok CLI/agent billing interface over scraping terminal output.
- Copilot exposes account quota snapshots through its supported account quota interface, including `remainingPercentage` and reset information. Use the percentage directly. Session `/usage` token or AI-credit totals are not account availability and shall not be used for this feature.

Provider interfaces can evolve. Keep provider-specific acquisition and parsing behind separate adapters and normalise only after the provider value has been identified explicitly as used or remaining.

## Acceptance criteria

1. `agentSessions --usage` is accepted by the existing command without changing the normal session-listing behaviour.
2. The command queries Claude, Codex, Grok and Copilot independently so failure of one provider does not prevent the others being reported.
3. Every numeric percentage printed by `--usage` means percentage available/remaining.
4. A provider value labelled as used/consumed is converted using `100 - used`, clamped to the range 0–100.
5. A provider value already labelled as remaining/available is used directly, clamped to the range 0–100.
6. Raw credits, tokens, request counts or costs are never presented as the primary availability value and are not used to manufacture a percentage unless the provider supplies an explicit total entitlement that makes the calculation authoritative.
7. Multiple independently binding windows are preserved, including short/session and weekly windows where supplied.
8. Reset date/time is displayed for each quota window when supplied by the provider.
9. Missing or unsupported account-wide quota data is shown as `UNKNOWN`; zero availability is shown as `0%` and is not confused with unknown data.
10. Not-installed and not-authenticated providers are reported distinctly from `UNKNOWN` and `0%`.
11. Provider adapters do not print, persist or log authentication tokens or credential-file contents.
12. Tests cover conversion from used to available, already-remaining values, 0%, 100%, missing fields, malformed responses, provider failure isolation, reset handling and mixed provider window shapes.
13. Tests verify that existing `agentSessions` listing, filtering, search, history and resume behaviour remains unchanged.
14. Documentation describes `agentSessions --usage`, defines percentages as available/remaining, and explains `UNKNOWN`, authentication and provider-specific windows.

## Out of scope

- Purchasing credits or changing plans.
- Resetting allowances.
- Predicting how long a future task will consume.
- Comparing model quality or recommending an agent solely from quota.
- Scraping browser account pages when a supported local CLI/SDK/protocol is available.
