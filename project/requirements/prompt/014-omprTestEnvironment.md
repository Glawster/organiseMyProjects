# 014: Implement the OMPR test environment

Implement requirement 014,
[OMPR test environment](../features/014-omprTestEnvironment.md).
The requirement is authoritative for scope and acceptance criteria 1–7.

Replace `environment.yml` with `organiseMyProjectsEnvironment.yml`, defining the
`organiseMyProjects` Conda environment with `-e .[dev]`, and update
`MANIFEST.in` and `.github/additional-instructions.md`. Make tests that need
`textual` use `pytest.importorskip("textual")` or an equivalent marker so they
skip with a clear reason outside the environment. Document environment set-up
in `documentation/testingProcess.md`, and make the release checklist in
`documentation/howToRelease.md` run inside that environment with no
dependency-related skips.

Constraints:

- Do not change OMPR runtime dependencies.
- Do not change how `manageProject` handles downstream environment files.

Allowed files: `organiseMyProjectsEnvironment.yml`, `environment.yml`,
`MANIFEST.in`, `.github/additional-instructions.md`,
`tests/test_sharedTuiStyles.py` and any other test needing an optional
dependency, `documentation/testingProcess.md` and
`documentation/howToRelease.md`.

Verify with:

```bash
conda env create -f organiseMyProjectsEnvironment.yml
conda run -n organiseMyProjects pytest -rs
pytest -rs   # from an environment without textual
runLinter --markup
```

Hand off with both pytest summaries, including the skip report, and the
markup lint result.
