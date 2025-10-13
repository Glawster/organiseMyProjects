# Git Commands Summary

## 🛠 Setup
```bash
git config --global user.name "Andy Wilson"
git config --global user.email andyw@glawster.com
git config --global core.editor "code --wait"
git config --global diff.tool code
git config --global autocrlf true
git init
git add --all
git status -s
git commit -m "Initial commit"
git config -e
```

## 🌐 Remotes
```bash
# Check configured remotes
git remote -v

# Remove and re-add remote
git remote remove origin
git remote add origin https://github.com/Glawster/organiseMyProjects.git

# Set branch to main and push
git branch -M main
git push -u origin main
```

## Branches
```bash
# Prune Remote Tracking References
git fetch -prune

# List Local Branches Not on Remote

git branch -vv | grep ': gone]'

# Delete Those Local Branches

You can delete them manually one by one:

git branch -d branch-name
```


## 🔄 Sync with GitHub
```bash
# Force overwrite local with GitHub (wipe local changes)
git fetch origin
git reset --hard origin/main
git clean -fd

# Merge GitHub and local unrelated histories
git pull origin main --allow-unrelated-histories
git push -u origin main

# Force push local over GitHub (dangerous - overwrites GitHub)
git push -u origin main --force
```

## 📂 File Management
```bash
# List files tracked by Git
git ls-files

# Show working directory status (tracked/untracked/ignored)
git status --short
git status --ignored

# Show files in the latest commit
git ls-tree --name-only -r HEAD
```

## Undoing Changes and Commits
```bash
# Undo changes to a file (revert back to last commit)
git checkout -- path/to/file

# Unstage a file (keep changes)
git reset HEAD path/to/file

# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# Undo last commit (keep changes unstaged)
git reset --mixed HEAD~1

# Undo last commit completely (discard changes)
git reset --hard HEAD~1

# Create a new commit that reverts a previous commit
git revert <commit-hash>

# Amend the most recent commit
git commit --amend -m "New commit message"

# Stash your changes (save for later without committing)
git stash          # save changes
git stash list     # view stashes
git stash pop      # re-apply last stash and remove it
git stash apply    # re-apply last stash but keep it in the stash list
```
## 📜 Viewing Commit History
```bash
# Show commit history (one line per commit)
git log --oneline

# Show commit history with graph
git log --oneline --graph --decorate --all

# Show last 5 commits
git log -5 --oneline
```
## ⏪ Rewinding to a Specific Commit
```bash
# Checkout a past commit (detached HEAD)
git checkout <commit-hash>
(You’ll be in a “detached HEAD” state, not on a branch.)

# Create a new branch from that commit
git checkout -b new-branch <commit-hash>

# Reset current branch to an earlier commit

- Keep changes staged:
git reset --soft <commit-hash>

- Keep changes unstaged:
git reset --mixed <commit-hash>

- Discard changes entirely:
git reset --hard <commit-hash>

# Revert a single commit (safe for shared repos)
git revert <commit-hash>
(Creates a new commit that undoes the target commit.)
```