# OMPR runtime synchronisation

Local `ompr/` runtime deployment is disabled by default. An explicit
`--runtime` enables it and saves `localRuntime: true` in `project/project.yaml`.
`--no-runtime` disables it and safely removes managed copies after migration
checks. Update and local runtime sync retain saved preferences; remote sync
remains instruction-only unless a runtime flag is supplied.

See [Optional OMPR runtime](runtimeDeployment.md) for the authoritative commands,
preference precedence, packaging, migration, backup and remote sync contract.
The shared manifest is in `organiseMyProjects/runtimeDeployment.py`;
`runtimeSync.py` remains a compatibility API for historical marked copies.

Run focused verification with:

```bash
python -m pytest tests/test_runtimePreference.py tests/test_runtimeDeployment.py tests/test_runtimeSync.py
```
