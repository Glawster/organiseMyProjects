# Requirement: 007 — project/requirements/features/007-linterWhitelistAndDigitNames.md

Role: implement and verify for OMP 0.8.

Read the authoritative requirement and existing GUI naming linter tests before
changing behaviour. Add a central exact-match whitelist for approved proper
names/acronyms used in logging case checks, initially including `DJI`,
`Firefox`, `GoPro`, `Grok`, `MCM`, `SQLite`, `TVDB`, and `X.ai`.

Do not weaken logging case validation globally. Preserve whitelisted tokens
while evaluating the remaining message text against the existing info/warning
and error casing rules.

Update module-level domainAction validation so digits are permitted within
otherwise valid names, including `_mp4BoxIterate` and `_mp4MvhdCreationRead`.
Preserve existing behaviour for nested helpers, class methods, framework
exceptions, test helpers, and logging interpolation restrictions.

Add focused regression tests and verify with:

- `pytest tests/test_guiNamingLinter.py`
- `pytest`
- `git diff --check`
