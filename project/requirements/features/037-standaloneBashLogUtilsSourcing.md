# 037: Standalone Bash logUtils sourcing

## Status

ToDo

## Outcome

As a maintainer of standalone Bash scripts (for example personal scripts in
`~/bin` that are not part of an OMP project), I need managed guidance for
sourcing `logUtils.sh` that works from any working directory and fails loudly,
so that a script never exits silently because its logging dependency could not
be found.

## Context

The Bash logging section of `.github/agent-instructions.md` has these gaps:

- Release 0.9 told scripts to locate the package with
  `source "$(python3 -c 'import organiseMyProjects, os; ...')/logUtils.sh"`.
  That `python3` only finds the package when the right Conda environment is
  active. In `~/bin` the environment is activated by direnv, so
  `wowAddonHelper.sh` worked only when run from `~/bin`. Elsewhere, the failed
  command substitution under `set -euo pipefail` ended the script with exit
  status 1 and no output, because `2>/dev/null` hid the Python error.
- Release 0.10 replaced the example with
  `source "${applicationRoot}/ompr/logUtils.sh"`. That needs a project with the
  ompr runtime deployed, which is opt-in since requirement 030. It gives
  standalone scripts no way to set `applicationRoot`, and under `set -u` an unset
  `applicationRoot` aborts the script.
- The section still says scripts source `logUtils.sh` "from the
  `organiseMyProjects` package", which does not match the runtime-copy example.
- The "No fallback logging" rule shows only Python. It does not say how a Bash
  script should fail fast with a clear message, or whether an existing
  shell-function fallback, like the one in `wowAddonHelper.sh`, is allowed.

## Scope

- Define how standalone Bash scripts locate `logUtils.sh` from the installed
  `organiseMyProjects` package without depending on the current directory or an
  activated environment (for example, an explicit interpreter path or another
  documented resolution order).
- Keep the project-runtime form (`${applicationRoot}/ompr/logUtils.sh`) for OMP
  projects, and state when each form applies.
- Specify fail-fast behaviour for Bash: under `set -euo pipefail`, a failed
  lookup must print an actionable error naming what was missing, never exit
  silently.
- State the Bash equivalent of the "No fallback logging" rule, including whether
  local stub logging functions are permitted.
- Make the section's wording consistent with the chosen sourcing forms.

## Out of scope

- Changes to the `logUtils.sh` logging API (`setApplication`, `log_*`
  functions).
- Automatically rewriting existing consumer scripts.
- Python logging guidance, apart from aligning the shared fail-fast wording.

## Acceptance criteria

1. Given a standalone script that follows the guidance, when it runs from a
   directory where no Conda environment is active, then it sources `logUtils.sh`
   successfully.
2. Given the package or interpreter cannot be found, when the script runs under
   `set -euo pipefail`, then it exits non-zero with an error message that names
   the missing dependency.
3. Given an OMP project with the ompr runtime enabled, when a script follows the
   project form, then sourcing behaves as it does in 0.10.
4. Given the Bash logging section, when a maintainer reads it, then it names
   which sourcing form applies to standalone scripts and which to project
   scripts, and states the Bash fallback rule.

## Dependencies and decisions

- Requirement 002 (ompr runtime infrastructure) and requirement 030 (opt-in
  local runtime) define the project-runtime form.
- An ADR may be needed if the standalone resolution order becomes a supported
  contract.

## Verification

- Bash tests that run a guidance-conformant script from an unrelated directory
  with no Conda environment active, and with the dependency missing, checking
  exit status and stderr.
- Documentation review of the Bash logging and "No fallback logging" sections
  against acceptance criterion 4.

## Change history

- 2026-11-25: created. Source: `~/bin/wowAddonHelper.sh` exited silently when
  run outside `~/bin` because the 0.9 `python3` lookup failed under `set -e`
  without the direnv-activated Conda environment.
