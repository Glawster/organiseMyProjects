# WoW addon standard

This managed guide defines how OMP World of Warcraft addon repositories are laid
out, checked and released. It applies to repositories whose role is
`wow-addon`: those with a `.toc` file at the repository root. Create one with:

```bash
manageProject create --project MyAddon --wow-addon --flavour retail -y
```

`--flavour` is `retail`, `classic` or `forever`; it sets the `.toc` Interface
number and the client folder the addon belongs in. `manageProject update` keeps
an existing addon's managed files current and never adds Python scaffolding.

## The repository is the addon folder

The game loads an addon from `Interface/AddOns/<Name>/<Name>.toc`, so the
repository root is the addon folder:

```text
MyAddon/
  MyAddon.toc            addon manifest: metadata and load order
  MyAddon.lua            entry point (namespace, saved variables, slash command)
  <area>/*.lua           further Lua, grouped in folders by concern (core/, ui/, Classes/ ...)
  Libs/                  embedded third-party libraries, if any (not linted)
  README.md              what the addon does, its commands, installation
  CHANGELOG.md           one section per released version
  .pkgmeta               release packaging: what ships and what is left out
  .luacheckrc            lint configuration (managed core + the addon's globals)
  stylua.toml            formatting
  .pre-commit-config.yaml
  MyAddonEnvironment.yml the `wow` Conda environment with the Lua tooling
  .envrc                 direnv: activates the `wow` environment on cd
  .github/ documentation/ project/   OMP agent, documentation and planning files
```

Rules:

- The folder name, the `.toc` file name and the addon name are identical.
- Lua and the `.toc` are the product. Everything else is development material
  and is excluded from release packages by `.pkgmeta`.
- Python tooling, such as a test harness, lives in its own subfolder with its
  own requirements; the addon role does not get a root Python package,
  `pyproject.toml` or `ompr/` runtime.

## Where the checkout lives

Clone the repository straight into the client's AddOns folder:

| Flavour | Client folder |
|---|---|
| retail | `_retail_/Interface/AddOns/<Name>` |
| classic | `_classic_era_/Interface/AddOns/<Name>` |
| forever | `_forever_/Interface/AddOns/<Name>` |

Do not symlink the addon folder into AddOns: under Wine the client does not list
symlinked addon folders. A symlink in the other direction, from `~/Source/<Name>`
to the checkout, is fine for editors and scripts.

## The .toc file

Every addon's `.toc` carries these fields:

| Field | Value |
|---|---|
| `## Interface` | The client's interface number; comma-separate several for multi-flavour addons. |
| `## Title` | The display name. |
| `## Notes` | One line describing the addon. |
| `## Author` | `Glawster`. |
| `## Version` | Semantic version, matching the latest `CHANGELOG.md` section and git tag. |
| `## Category` | The AddOns-list category, e.g. `Combat`, `Inventory`, `Professions`. |
| `## SavedVariables` | `<Name>DB` when the addon saves account-wide settings. |

Use `## SavedVariablesPerCharacter: <Name>CharDB` for per-character data. List
the Lua files after the metadata in load order; use backslashes or forward
slashes consistently for subfolders.

## Lua conventions

- Start each file with `local addonName, ns = ...` and share state through
  `ns`, not globals. The only globals an addon sets are its SavedVariables,
  slash-command names (`SLASH_<NAME>1`) and `SlashCmdList` entries, and key
  bindings; list each one in `.luacheckrc` under `globals`.
- Initialise saved variables on `ADDON_LOADED` for the addon's own name,
  filling in defaults for missing keys.
- Use `camelCase` for locals and functions, `PascalCase` for module tables, and
  `UPPER_CASE` for constants.
- Use the `.toc` `## Version` as the single source of the version number.

## Tooling

The `wow` Conda environment (`<Name>Environment.yml`) provides Lua 5.1 (the
game's Lua version), luarocks, StyLua and pre-commit. luacheck is not packaged
for Conda, so install it once through luarocks:

```bash
conda env update -n wow -f MyAddonEnvironment.yml
conda activate wow
luarocks install luacheck
pre-commit install
pre-commit run --all-files    # first run: formats and lints everything
```

With direnv, `.envrc` activates the environment whenever you enter the
repository (`layout conda wow`, using the `layout_conda` helper in
`~/.config/direnv/direnvrc`); run `direnv allow` once per checkout. luacheck
builds a small C library (luafilesystem) when installed, so it needs `gcc`.

The pre-commit hooks run:

- **luacheck**: syntax errors, accidental global writes, unused variables and
  shadowing. Reading undefined globals is not reported, because the WoW API is
  thousands of globals.
- **StyLua**: formatting to `stylua.toml` (4-space indent, 120 columns, double
  quotes).

Commit with the `wow` environment active so the hooks can find both tools.

## Testing

There is no game client in CI, so an addon is tested in two layers:

1. **Static**: the luacheck and StyLua hooks on every commit. To check that the
   files load, run them with `lua` and stub WoW globals for the API the file
   uses at load time.
2. **In game**: `/reload` after changes, with Lua errors shown
   (`/console scriptErrors 1`). Record what you checked in the change's
   requirement or pull request.

## Releasing

1. Update `## Version` in the `.toc` and add a `CHANGELOG.md` section.
2. Commit, then tag the commit `v<version>` and push the tag.
3. To build a zip, run the BigWigs packager
   (`release.sh` from `BigWigsMods/packager`). It reads `.pkgmeta`, leaves the
   development files out, and writes the package to `.release/`.

See [howToRelease.md](howToRelease.md) for the shared branch and tag process.
