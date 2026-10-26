# 026: Implement shared TUI style mockup

## Assignment

Implement and verify [requirement 026](../features/026-sharedTuiStyleMockup.md).
The requirement is authoritative for scope and acceptance criteria.

## Boundaries

Render a headless, reproducible SVG through Textual and `myStyles.css` at the
fixed path `output/myStyles.svg`. Keep the artifact ignored; do not add an
inline colour palette, upload images or change production application data.
Use `styles/projectStyles.css` as the project-owned override, producing
`output/projectStyles.svg`; otherwise use OMP's canonical stylesheet.

## Verification and handoff

Run the focused mockup and shared-style tests, Black, runLinter and git
diff --check. Generate an SVG and report its path and the represented controls.
