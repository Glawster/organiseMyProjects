"""
wowAddon.py

Scaffold content for the ``wow-addon`` project role: World of Warcraft addons
written in Lua. An addon repository *is* the addon folder, so its ``.toc`` and
Lua files sit at the repository root and it carries no Python package.

The file templates live here; manageProject wires them into create and update.
See documentation/wowAddon.md for the standard these files implement.
"""

from pathlib import Path

ROLE = "wow-addon"

# Game flavours: the client folder under the WoW install, and the ``## Interface``
# number a new addon starts with. Update the numbers as the game patches.
FLAVOURS = {
    "retail": {"folder": "_retail_", "interface": "120001"},
    "classic": {"folder": "_classic_era_", "interface": "11507"},
    "forever": {"folder": "_forever_", "interface": "16001"},
}
DEFAULT_FLAVOUR = "retail"
DEFAULT_AUTHOR = "Glawster"


def addonTocFind(basePath: Path) -> Path | None:
    """Return the addon's root ``.toc`` file, preferring one named after the folder."""
    tocs = sorted(basePath.glob("*.toc"))
    if not tocs:
        return None
    for toc in tocs:
        if toc.stem.casefold() == basePath.resolve().name.casefold():
            return toc
    return tocs[0]


def isWowAddon(basePath: Path) -> bool:
    """Return whether basePath is a WoW addon repository (a ``.toc`` at its root)."""
    return addonTocFind(basePath) is not None


def addonNameFor(projectName: str | Path) -> str:
    """Return the addon name: the folder name, which must match the ``.toc`` stem."""
    return Path(projectName).name


def savedVariablesName(addonName: str) -> str:
    """Return the standard SavedVariables table name for an addon."""
    return f"{addonName}DB"


def slashName(addonName: str) -> str:
    """Return the SlashCmdList key for an addon."""
    return "".join(ch for ch in addonName.upper() if ch.isalnum())


def tocContentBuild(addonName: str, flavour: str = DEFAULT_FLAVOUR) -> str:
    """Return a new addon's ``.toc``: standard metadata, then the files to load."""
    interface = FLAVOURS[flavour]["interface"]
    return (
        f"## Interface: {interface}\n"
        f"## Title: {addonName}\n"
        f"## Notes: Describe {addonName} in one line.\n"
        f"## Author: {DEFAULT_AUTHOR}\n"
        "## Version: 0.1.0\n"
        "## Category: Miscellaneous\n"
        f"## SavedVariables: {savedVariablesName(addonName)}\n"
        "\n"
        f"{addonName}.lua\n"
    )


def mainLuaContentBuild(addonName: str) -> str:
    """Return the starter Lua file: namespace, saved variables, slash command."""
    db = savedVariablesName(addonName)
    slash = slashName(addonName)
    command = addonName.lower()
    return f"""-- {addonName}/{addonName}.lua
-- Entry point: the addon namespace, saved variables and the /{command} command.

local addonName, ns = ...

local Addon = {{}}
ns.Addon = Addon

local DEFAULTS = {{}}

function Addon.Print(...)
    print("|cff66ccff" .. addonName .. "|r:", ...)
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", function(self, event, name)
    if event == "ADDON_LOADED" and name == addonName then
        {db} = {db} or {{}}
        for key, value in pairs(DEFAULTS) do
            if {db}[key] == nil then
                {db}[key] = value
            end
        end
        Addon.db = {db}
        self:UnregisterEvent("ADDON_LOADED")
    end
end)

SLASH_{slash}1 = "/{command}"
SlashCmdList.{slash} = function(msg)
    Addon.Print("loaded", msg or "")
end
"""


LUACHECK_MANAGED_BLOCK = """std = "lua51"
max_line_length = false
codes = true
exclude_files = { ".git/", ".luarocks/", "lua_modules/", "Libs/", "libs/" }
-- WoW's API is thousands of globals; reading an undefined global (113) is not
-- reported. Writing one (111) or mutating one (112, 122) is: that is the classic
-- addon bug. List the globals the addon deliberately sets in `globals` below.
ignore = { "113", "212/self", "211/_.*", "212/_.*", "213/_.*" }"""


def luacheckrcContentBuild(addonName: str) -> str:
    """Return ``.luacheckrc``: a managed core, then the addon's own globals."""
    slash = slashName(addonName)
    return (
        "-- OMP-MANAGED-BEGIN\n"
        f"{LUACHECK_MANAGED_BLOCK}\n"
        "-- OMP-MANAGED-END\n"
        "\n"
        "-- Globals this addon sets: SavedVariables, slash commands, bindings.\n"
        "globals = {\n"
        f'    "{savedVariablesName(addonName)}",\n'
        f'    "SLASH_{slash}1",\n'
        '    "SlashCmdList",\n'
        "}\n"
    )


STYLUA_CONTENT = """column_width = 120
line_endings = "Unix"
indent_type = "Spaces"
indent_width = 4
quote_style = "AutoPreferDouble"
call_parentheses = "Always"
"""

PRECOMMIT_MANAGED_BLOCK = """  - repo: local
    hooks:
      - id: luacheck
        name: luacheck
        entry: luacheck
        language: system
        types: [lua]
      - id: stylua
        name: StyLua
        entry: stylua
        language: system
        types: [lua]"""

PRECOMMIT_CONTENT = f"""repos:
  # OMP-MANAGED-BEGIN
{PRECOMMIT_MANAGED_BLOCK}
  # OMP-MANAGED-END
"""

ENVIRONMENT_MANAGED_BLOCK = """  - lua=5.1
  - luarocks
  - stylua
  - pre-commit"""

ENVIRONMENT_CONTENT = f"""name: wow
channels:
  - conda-forge
dependencies:
  # OMP-MANAGED-BEGIN
{ENVIRONMENT_MANAGED_BLOCK}
  # OMP-MANAGED-END
# luacheck is not packaged for Conda; after creating the environment run:
#   luarocks install luacheck
"""

VSCODE_MANAGED_BLOCK = """   "Lua.runtime.version": "Lua 5.1",
   "Lua.workspace.checkThirdParty": false,
   "Lua.diagnostics.disable": ["undefined-global"],
   "files.associations": { "*.toc": "ini" }"""

VSCODE_SETTINGS_CONTENT = f"""{{
   // OMP-MANAGED-BEGIN
{VSCODE_MANAGED_BLOCK}
   // OMP-MANAGED-END
}}
"""

ENVRC_CONTENT = """# direnv: activate the wow Conda environment (Lua 5.1, luarocks, luacheck, StyLua,
# pre-commit) on cd. Uses layout_conda from ~/.config/direnv/direnvrc.
# Run `direnv allow` once.
layout conda wow
"""

GITIGNORE_CONTENT = """# packaging output
.release/
*.zip
# local Lua tooling
.luarocks/
lua_modules/
"""

# Development files left out of a packaged release (.pkgmeta `ignore`).
PACKAGE_IGNORE = [
    ".github",
    ".vscode",
    "documentation",
    "project",
    "tests",
    "AGENTS.md",
    "CLAUDE.md",
    "projectGuidelines.md",
    ".luacheckrc",
    "stylua.toml",
    ".pre-commit-config.yaml",
    ".envrc",
]


def pkgmetaContentBuild(addonName: str) -> str:
    """Return ``.pkgmeta`` for the BigWigs/CurseForge packager."""
    ignore = PACKAGE_IGNORE + [f"{addonName}Environment.yml"]
    lines = "\n".join(f"  - {entry}" for entry in ignore)
    return f"package-as: {addonName}\n\nignore:\n{lines}\n"


def environmentFileName(addonName: str) -> str:
    """Return the addon's Conda environment file name."""
    return f"{addonName}Environment.yml"


CHANGELOG_CONTENT = """# Changelog

## 0.1.0

- First version.
"""


def readmeContentBuild(addonName: str, flavour: str = DEFAULT_FLAVOUR) -> str:
    """Return a new addon's README."""
    folder = FLAVOURS[flavour]["folder"]
    command = addonName.lower()
    return f"""# {addonName}

Describe what {addonName} does.

## Commands

| Command | What it does |
|---|---|
| `/{command}` | Describe the command. |

## Installation

Clone the repository straight into the game's AddOns folder (the repository is
the addon folder), then restart the game:

```bash
cd "<WoW install>/{folder}/Interface/AddOns"
git clone git@github.com:{DEFAULT_AUTHOR}/{addonName}.git
```

## Development

See [documentation/wowAddon.md](documentation/wowAddon.md) for the layout,
tooling and release process. Use the `wow` Conda environment
(`{environmentFileName(addonName)}`) and commit with it active, so the
luacheck and StyLua pre-commit hooks can run. To check every file:

```bash
pre-commit run --all-files
```

Then `/reload` in game with Lua errors shown (`/console scriptErrors 1`).

## Documentation

- [WoW addon standard](documentation/wowAddon.md)
- [Repository Layout](documentation/repositoryLayout.md)
- [Requirements Management](documentation/requirementsManagement.md)
- [Current Increment](project/currentIncrement.md)
- [Changelog](CHANGELOG.md)
"""


def projectYamlContentBuild(
    addonName: str,
    flavour: str = DEFAULT_FLAVOUR,
    version: str = "0.1.0",
    description: str = "World of Warcraft addon",
) -> str:
    """Return ``project/project.yaml`` for an addon."""
    description = description.replace('"', "'")
    return (
        f'name: "{addonName}"\n'
        f'description: "{description}"\n'
        f'version: "{version}"\n'
        'runtime: "lua5.1"\n'
        f'role: "{ROLE}"\n'
        f'flavour: "{flavour}"\n'
    )


def tocFieldsRead(tocPath: Path) -> dict[str, str]:
    """Return the ``## Key: value`` metadata of a ``.toc`` file."""
    fields = {}
    for raw in tocPath.read_text(encoding="utf-8-sig").splitlines():
        if raw.startswith("##") and ":" in raw:
            key, _, value = raw[2:].partition(":")
            fields[key.strip()] = value.strip()
    return fields


def flavourDetect(interface: str) -> str:
    """Return the flavour a ``## Interface`` number belongs to (first one if several)."""
    first = interface.split(",")[0].strip()
    if first == FLAVOURS["forever"]["interface"] or first.startswith("160"):
        return "forever"
    if first.isdigit() and int(first) < 20000:
        return "classic"
    return "retail"


REQUIRED_TOC_FIELDS = ("Interface", "Title", "Notes", "Author", "Version")
