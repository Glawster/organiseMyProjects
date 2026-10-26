# 026: Shared TUI style mockup

## Status

Completed

## Outcome

As a maintainer of the shared Textual theme, I need to generate an SVG mockup
from `myStyles.css` so that I can review ordinary component styling after every
theme change.

## Context

The shared stylesheet defines colours, controls and reusable surfaces but has
no visual artifact that demonstrates their combined appearance. A deterministic
headless render makes theme changes reviewable without a manually operated UI.

## Scope

- Add a `styleMockup` command that writes `output/myStyles.svg`, derived from
  the canonical stylesheet name.
- Use `styles/projectStyles.css` as the explicit project-owned override;
  otherwise use OMP's canonical stylesheet.
- Render ordinary panels, lists, inputs, select controls, buttons, a table and
  success, warning and error states using `myStyles.css`.
- Use a fixed headless Textual size so regenerated SVGs are comparable.

## Out of scope

- A new interactive application or permanent graphical demo.
- Screenshot comparison approval, image upload or automatic style changes.
- Styling component-specific production data.

## Acceptance criteria

1. Given Textual is installed, when `styleMockup` runs without a project
   stylesheet, then it writes a non-empty SVG containing the shared-theme
   showcase to `output/myStyles.svg`.
2. Given the generated SVG, when it is inspected, then it contains
   representative panels, list, input, select, buttons, table and semantic
   success, warning and error content.
3. Given a stylesheet change, when the generator is rerun, then it uses the
   changed `myStyles.css` without an inline duplicate palette.
4. Given a repository with `styles/projectStyles.css`, when the generator runs,
   then it renders that stylesheet to `output/projectStyles.svg` instead of
   OMP's theme.
5. Given Textual is unavailable, when the command runs, then it fails with a
   clear installation message and does not write an artifact.

## Dependencies and decisions

- Depends on requirement 012's shared Textual styling.
- No ADR required.

## Verification

- pytest tests/test_styleMockup.py and tests/test_sharedTuiStyles.py
- Run `styleMockup`
- Inspect the SVG for all representative component labels.

## Change history

- 2026-10-25: created — generate a reusable shared-style mockup.
- 2026-10-25: fixed output name to output/myStyles.svg.
- 2026-10-25: select a project-owned stylesheet override when present.
- 2026-10-25: locate project-owned styles only at styles/projectStyles.css.
- 2026-10-25: status InProgress -> Completed — myBoard.
