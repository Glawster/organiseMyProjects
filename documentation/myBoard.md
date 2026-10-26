# Requirement board

`myBoard` shows and updates the requirements of the project it is run from.
The command is installed with organiseMyProjects. It is not copied into other
repositories.

## Where it looks

`myBoard` walks up from the current directory and uses the nearest directory
that contains `project/requirements/requirementsIndex.md`. In a repository
with more than one project, that nearest project wins. `--project` selects a
different root.

## Columns

Each requirement appears in one column:

| Column | What it shows |
| --- | --- |
| Backlog | Status `ToDo`, and not listed on the current increment |
| ToDo | Status `ToDo`, and listed on the current increment |
| InProgress | Status `InProgress` |
| Completed | Status `Completed` |

Moving between Backlog and ToDo keeps the status as `ToDo` and changes
`project/currentIncrement.md`. Moving to InProgress or Completed also updates
the requirement's `## Status` section, its change history, and the status cell
in `requirementsIndex.md`. A move between Backlog and InProgress does both.

The default is a dry-run. `--confirm` writes the files. The board asks before
it writes. `myBoard` does not commit.

## Commands

```bash
myBoard
myBoard list
myBoard list --json
myBoard show 012
myBoard move 012 InProgress
myBoard move 012 InProgress --confirm
myBoard edit 012 --outcome "As a ..." --confirm
myBoard create --name myBoard --title "Requirement board" \
  --description "One index sentence." --outcome "As a ..." --confirm
myBoard check
myBoard check 012
myBoard lint
myBoard pytest
```

`list`, `show`, `move`, `create` and `edit` work without Textual. The board
itself needs the `tui` extra, which is already included in the `dev` extra:

```bash
pip install 'organiseMyProjects[tui]'
```

## Editing

`myBoard edit NUMBER` updates only fields supplied as options:

| Option | Replaces |
| --- | --- |
| `--title` | The record heading, index link and any increment or backlog bullet |
| `--description` | The index description |
| `--outcome` | Outcome |
| `--context` | Context |
| `--scope` | Scope |
| `--excluded` | Out of scope |
| `--acceptance` | Acceptance criteria |
| `--dependencies` | Dependencies and decisions |
| `--verification` | Verification |

```bash
myBoard edit 023 --outcome "As a ..."             # list the files it would change
myBoard edit 023 --outcome "As a ..." --confirm   # write them
```

Without `--confirm` the command only lists the files it would write. A
confirmed edit appends a dated `edited — myBoard.` entry to the record's
change history. A section the record does not have yet is added in the
standard template order. The requirement number, filename and Status never
change; use `myBoard move` to change Status.

The command refuses, with exit status 1 and no files changed, when no field is
given, a value is blank, or a value would break the index table. Titles and
descriptions must be a single line without `|`, and titles cannot contain `[`
or `]`.

## Board keys

| Key | Action |
| --- | --- |
| Left, Right | Move between columns |
| Up, Down, or right click | Select a card |
| Enter, or left click | Open the selected card |
| `[`, `]` | Move the selected card one column, after confirmation. On an open requirement these keys do nothing |
| `c` | Run `manageProject` checks |
| `n` | Run `runLinter` |
| `p` | Run pytest |
| `g` | Reload the board and the Git strip |
| `q` | Quit |

The lower half of the board is a scrollable status panel. It shows each useful
status item on its own line: project, current branch and work-tree state,
divergence from `main` and the increment's release branch, every unmerged local
or remote-only branch with its OMP version, and checks, lint and pytest
summaries. `myBoard list` prints the same Git summary before the columns. A
branch without
`organiseMyProjects/version.py` reports its version as unavailable. Checks,
lint and pytest stay blank until you ask for them.

The card shows the branch whose name contains the requirement id, and the
branch that still holds an unmerged commit for it. Commits from that mention
to the branch tip are listed. Each changed file is on its own line. Check findings that name the requirement are
listed on the card. Lint findings are listed when they sit in a file changed
on one of those branches. Pytest failures are listed when they name one of
those files or a path in the requirement's Verification section. The suite
summary stays on the strip. A `!` on a card means the record status and the
index status disagree. Moving the card writes both.

## What the board does not do

The board screen does not edit requirement prose (use `myBoard edit`), open
pull requests, infer a column from Git or from test results, or commit the
documents it writes.
