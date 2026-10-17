# 011: Implement repository and project root awareness

Implement requirement 011, Repository and project root awareness.

Update `manageProject check` so it distinguishes the selected project root from the containing Git repository root. Repository-owned checks, including `ENT-001`, `ENT-002`, and `ENT-003`, must resolve their files from the Git repository root, while project-owned checks continue to resolve from the selected project root.

Use Git work-tree discovery equivalent to `git rev-parse --show-toplevel`, preserve current behaviour when both roots are the same, provide deterministic fallback outside Git repositories, and do not create or recommend duplicate repository-level files inside nested projects.

Add regression tests using a layout equivalent to:

```text
linuxMigration/
├── AGENTS.md
├── .github/
│   ├── copilot-instructions.md
│   └── additional-instructions.md
└── mailAgent/
    ├── pyproject.toml
    ├── src/
    └── tests/
```

Verify that valid root-level files satisfy the ENT checks when `mailAgent` is checked, that genuinely missing root-level files are reported against repository-root paths, and that project-scoped checks still use `mailAgent` as their root.
