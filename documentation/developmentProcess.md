# Development Process

## Purpose

This document defines the standard development workflow for all repositories managed using organiseMyProjects guidance.

The goal is to keep feature work flexible while keeping `main` concise, reviewable and easy to understand.

## Standard branch workflow

All normal development work must be performed on a dedicated branch created from the current `main` branch.

Use a branch name that describes the work, for example:

```text
feature/009-read-inbox-filing
feature/shared-media-primitives
release/0.8
chore/adopt-process-standards
```

Before creating the branch, update local `main` from its remote and ensure the working tree is clean.

Typical local workflow:

```bash
git switch main
git pull --ff-only
git switch -c feature/example-change
git push -u origin feature/example-change
```

Development branches may contain multiple implementation, test, review and fix-up commits while work is in progress.

## Validation before integration

Before integrating a completed branch into `main`, run the checks appropriate to the repository.

For Python projects managed with organiseMyProjects this normally includes:

```bash
pytest
black --check .
runLinter
manageProject --check
```

Use the repository's own documented test and validation commands where they differ or add additional checks.

Relevant manual checks, UI checks, migration dry-runs or integration tests must also be completed before integration when the change requires them.

Do not integrate known failing work into `main`.

## Integration into main

A completed feature, requirement, release increment or coherent maintenance change should normally appear on `main` as one meaningful commit.

The preferred integration method is a pull request using **Squash and merge**.

When a pull request is not used, create an equivalent local or API-driven squash commit whose tree contains the completed branch state and whose parent is the current `main` head.

The resulting commit message should describe the completed unit of work, for example:

```text
Implement REQ-009 read Inbox filing
Add shared media primitives
Release organiseMyProjects 0.8
```

Do not fast-forward a development branch containing many intermediate commits directly onto `main` unless preserving those individual commits is an explicit exception for that repository or change.

## Keeping main current

`main` is the canonical integrated history.

After a squash integration:

- update local `main` from the remote;
- do not continue development on the already integrated branch;
- create subsequent work from the new `main` head;
- remove obsolete local and remote feature branches once they are no longer needed.

If `main` has been intentionally rewritten, local copies must be realigned explicitly rather than merged back into the rewritten history, for example:

```bash
git fetch origin
git switch main
git reset --hard origin/main
```

History rewrites of `main` are exceptional. Normal completed work should enter `main` through a squash merge rather than by repeatedly rewriting existing integrated history.

## Pull request expectations

Where pull requests are used:

- the PR base is `main`;
- the PR head is the dedicated development branch;
- automated and manual checks should be complete before merge;
- review findings are fixed on the development branch;
- the final integration method is **Squash and merge**;
- the squash commit message should describe the completed feature or requirement rather than an implementation step;
- the feature branch may be deleted after successful integration.

## Exceptions

A repository may document a justified exception in its project-specific instructions, but the default remains branch development followed by squash integration into `main`.

Examples where preserving multiple commits may be justified include externally maintained history, vendor imports or an intentionally structured release history.

An exception must be deliberate; it must not occur merely because a feature branch was fast-forwarded by convenience.

## Agent behaviour

When an automated coding agent performs repository work, it must follow the same process:

1. inspect the current repository and `main` state;
2. create or use the dedicated branch for the requested work;
3. make implementation commits on that branch;
4. keep the user informed of relevant commit hashes and validation status;
5. do not claim tests have run unless they have actually run;
6. complete required verification before integration;
7. squash the completed work into `main`, normally through a PR when that workflow is available;
8. begin later work from the updated `main` branch.

This workflow applies across the user's repositories unless repository-specific guidance explicitly defines an exception.
