# 018: Framework override naming exemptions beyond Textual

## Status

ToDo

## Outcome

As a developer subclassing a library class, I need `runLinter` to accept
method names that the base class dictates, so that I do not have to replace
correct standard-library code with workarounds to satisfy the naming rules.

## Context

Requirement 007 exempts Textual `action_*` and `on_*` handlers because their
spelling is dictated by the framework. No equivalent exemption exists for
other base classes.

On 2026-10-20, `mailAgent` added an `html.parser.HTMLParser` subclass for
reducing HTML mail to text. `runLinter` flagged `handle_starttag`,
`handle_endtag` and `handle_data` as method-naming violations. Renaming them
would stop `HTMLParser` calling them, so the working subclass was replaced
with regular expressions to pass the linter.

The same applies to other standard-library hooks such as
`BaseHTTPRequestHandler.do_GET`, `unittest.TestCase.setUp`/`tearDown`,
`logging.Handler.emit`, `ast.NodeVisitor.visit_*` and
`json.JSONEncoder.default`.

## Scope

- Exempt a method from method-naming rules when it overrides a method that
  exists on a base class imported from outside the project.
- Where the base class cannot be resolved statically, accept a centrally
  maintained, reviewable list of known protocol names and patterns, seeded with
  the standard-library hooks listed above.
- Keep requirement 007's Textual rules unchanged.
- Report the exemption reason in verbose output so it is reviewable.
- Document the policy and the list in the linter guidance distributed by OMPR.

## Out of scope

- Exempting arbitrary snake_case project methods.
- Exempting module-level functions.
- Resolving base classes through dynamic or runtime inspection.

## Acceptance criteria

1. Given a class deriving from `html.parser.HTMLParser` that defines
   `handle_starttag`, `handle_endtag` and `handle_data`, when `runLinter` runs,
   then no naming finding is reported for them.
2. Given a class deriving from `http.server.BaseHTTPRequestHandler` that
   defines `do_GET`, when linted, then no naming finding is reported.
3. Given a project class deriving from another project class that defines a new
   snake_case method, when linted, then the naming finding is still reported.
4. Given a snake_case method on a class with no external base, when linted,
   then the naming finding is still reported.
5. Given the existing Textual fixtures, when linted, then results are unchanged.

## Dependencies and decisions

- Extends requirement 007's framework and protocol exemption policy.
- Uses the requirement 013 finding and reporting format.
- No architecture decision is expected.

## Verification

- Fixture tests for each acceptance criterion.
- Run `runLinter` across downstream projects and confirm no new findings.

## Change history

- 2026-10-20: created — `mailAgent` replaced a working `HTMLParser` subclass
  to satisfy the linter; captured for the 0.9 backlog.
