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
myBoard create --name myBoard --title "Requirement board" \
  --description "One index sentence." --outcome "As a ..." --confirm
myBoard check
myBoard check 012
myBoard lint
myBoard pytest
```

`list`, `show`, `move` and `create` work without Textual. The board itself
needs the `tui` extra, which is already included in the `dev` extra:

```bash
pip install 'organiseMyProjects[tui]'
```

## Board keys

| Key | Action |
| --- | --- |
| Left, Right | Move between columns |
| Up, Down, or click | Select a card |
| Enter | Open the selected card |
| `[`, `]` | Move the selected card one column, after confirmation. On an open requirement these keys do nothing |
| `c` | Run `manageProject` checks |
| `n` | Run `runLinter` |
| `p` | Run pytest |
| `g` | Reload the board and the Git strip |
| `q` | Quit |

The strip above the columns shows the current branch, whether the work tree is
dirty, and how far the branch is ahead of or behind `main` and the release
branch named by the increment. Checks, lint and pytest stay blank until you
ask for them.

The card shows the branch whose name contains the requirement id, and the
branch that still holds an unmerged commit for it. Commits from that mention
to the branch tip are listed. Each changed file is on its own line. Check findings that name the requirement are
listed on the card. Lint findings are listed when they sit in a file changed
on one of those branches. Pytest failures are listed when they name one of
those files or a path in the requirement's Verification section. The suite
summary stays on the strip. A `!` on a card means the record status and the
index status disagree. Moving the card writes both.

## What the board does not do

It does not edit requirement prose, open pull requests, infer a column from
Git or from test results, or commit the documents it writes.
