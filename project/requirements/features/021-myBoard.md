# 021: Requirement board

## Status

InProgress

## Outcome

As a developer working in an OMP project, I need a board named myBoard so that I can see each requirement as Backlog, ToDo, InProgress or Completed and update the record, the index and the current increment together.

## Context

Requirements already live in project/requirements, with status in both the record and requirementsIndex.md, and the current schedule in project/currentIncrement.md. There was no view that showed Backlog beside ToDo or kept those documents aligned. The board also shows Git, manageProject check, runLinter and pytest evidence without using that evidence to choose a column.

## Scope

- Show Backlog, ToDo, InProgress and Completed for the nearest project that owns project/requirements.
- Move a card only after confirmation, updating the requirement record, requirementsIndex.md and project/currentIncrement.md together.
- Keep list, show, move and create usable without Textual, and open the board when Textual is installed.
- Show the current branch on the strip, and on request the manageProject check, runLinter and pytest results.

## Out of scope

- Editing requirement prose inside the board.
- Inferring a column from Git history or from test results.
- Opening pull requests or committing the documents the board writes.
- Copying myBoard into downstream repositories.

## Acceptance criteria

1. Given a project with requirements in each lifecycle state, when myBoard list runs, then each requirement appears in exactly one of Backlog, ToDo, InProgress or Completed.
2. Given a Backlog card, when it is moved to ToDo and confirmed, then its status stays ToDo, the current increment lists it, and the backlog section no longer does.
3. Given a ToDo card, when it is moved to InProgress and confirmed, then the record, the index and the increment all say InProgress.
4. Given a move without --confirm, when the command finishes, then it reports the files it would change and leaves them unchanged.
5. Given the board is opened in a project, when the strip is shown, then it names the current Git branch.
6. Given a request for checks on a card, when manageProject check has a finding for that requirement, then the card shows the rule id.

## Dependencies and decisions

- None.

## Verification

- pytest tests/test_myBoard.py
- runLinter on requirementBoard.py, myBoard.py and myBoardTui.py
- myBoard list, and a confirmed move of requirement 021

## Change history

- 2026-10-22: created — myBoard.
- 2026-10-22: status ToDo -> InProgress — myBoard.
