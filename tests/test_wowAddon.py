"""The wow-addon role: create, detect and update Lua addon repositories."""

import shutil
import subprocess

import pytest

from organiseMyProjects import wowAddon
from organiseMyProjects.agentCheck import AgentCheckValidator
from organiseMyProjects.manageProject import (
    _projectRoleDetect,
    createWowAddon,
    main,
    updateProject,
)


def _create(tmp_path, name="MyAddon", flavour="retail"):
    target = tmp_path / name
    createWowAddon(target, flavour=flavour)
    return target


def testCreateWritesAddonAtRepositoryRoot(tmp_path):
    addon = _create(tmp_path)
    for relative in [
        "MyAddon.toc",
        "MyAddon.lua",
        "README.md",
        "CHANGELOG.md",
        ".pkgmeta",
        ".envrc",
        ".luacheckrc",
        "stylua.toml",
        ".pre-commit-config.yaml",
        "MyAddonEnvironment.yml",
        ".vscode/settings.json",
        "AGENTS.md",
        ".github/agent-instructions.md",
        "documentation/wowAddon.md",
        "documentation/repositoryLayout.md",
        "project/project.yaml",
        "project/currentIncrement.md",
        "project/requirements/requirementsIndex.md",
    ]:
        assert (addon / relative).is_file(), relative


def testCreateAddsNoPythonScaffold(tmp_path):
    addon = _create(tmp_path)
    for relative in [
        "pyproject.toml",
        "pytest.ini",
        "ompr",
        "MyAddon/__init__.py",
        "tests",
        "documentation/tuiStyling.md",
        "documentation/linter.md",
        "myStyles.css",
    ]:
        assert not (addon / relative).exists(), relative


@pytest.mark.parametrize(
    "flavour,interface",
    [("retail", "120001"), ("forever", "16001"), ("classic", "11507")],
)
def testTocCarriesStandardFields(tmp_path, flavour, interface):
    addon = _create(tmp_path, flavour=flavour)
    fields = wowAddon.tocFieldsRead(addon / "MyAddon.toc")
    for key in wowAddon.REQUIRED_TOC_FIELDS:
        assert key in fields
    assert fields["Interface"] == interface
    assert fields["SavedVariables"] == "MyAddonDB"
    assert "MyAddon.lua" in (addon / "MyAddon.toc").read_text()
    assert f'flavour: "{flavour}"' in (addon / "project/project.yaml").read_text()


def testLuacheckDeclaresAddonGlobals(tmp_path):
    text = (_create(tmp_path) / ".luacheckrc").read_text()
    assert "-- OMP-MANAGED-BEGIN" in text
    for name in ['"MyAddonDB"', '"SLASH_MYADDON1"', '"SlashCmdList"']:
        assert name in text


def testPkgmetaLeavesDevelopmentFilesOut(tmp_path):
    text = (_create(tmp_path) / ".pkgmeta").read_text()
    assert text.startswith("package-as: MyAddon\n")
    for entry in ["documentation", "project", ".github", "MyAddonEnvironment.yml"]:
        assert f"  - {entry}\n" in text
    assert "MyAddon.lua" not in text


def testCreateRefusesUnknownFlavour(tmp_path):
    with pytest.raises(ValueError):
        createWowAddon(tmp_path / "MyAddon", flavour="wrath")


def testCreatedAddonPassesAgentCheck(tmp_path):
    addon = _create(tmp_path)
    subprocess.run(["git", "init", str(addon)], check=True, capture_output=True)
    report = AgentCheckValidator(addon).runAll()
    assert not report.failures, report.findings


def testRoleDetectedFromRootToc(tmp_path):
    (tmp_path / "Thing.toc").write_text("## Interface: 120001\n")
    # Python tooling in the repository does not change the role.
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    assert _projectRoleDetect(tmp_path) == "wow-addon"


def testTocInSubfolderIsNotAnAddon(tmp_path):
    (tmp_path / "Thing").mkdir()
    (tmp_path / "Thing" / "Thing.toc").write_text("## Interface: 120001\n")
    assert _projectRoleDetect(tmp_path) != "wow-addon"


def testUpdateExistingAddonAddsStandardWithoutPython(tmp_path):
    addon = tmp_path / "OldAddon"
    addon.mkdir()
    (addon / "OldAddon.toc").write_text(
        "## Interface: 16001\n## Title: Old\n## SavedVariables: OldAddonDB\n\nOld.lua\n"
    )
    (addon / "Old.lua").write_text("print('hi')\n")
    (addon / "README.md").write_text("# Old addon\n")

    updateProject(addon)

    assert (addon / "README.md").read_text() == "# Old addon\n"
    assert (addon / "Old.lua").read_text() == "print('hi')\n"
    for relative in [
        ".luacheckrc",
        ".pkgmeta",
        "stylua.toml",
        "documentation/wowAddon.md",
    ]:
        assert (addon / relative).is_file(), relative
    assert not (addon / "pyproject.toml").exists()
    assert not (addon / "OldAddon" / "__init__.py").exists()


def testUpdateReplacesOnlyTheManagedPrecommitBlock(tmp_path):
    addon = _create(tmp_path)
    config = addon / ".pre-commit-config.yaml"
    config.write_text(
        "repos:\n"
        "  - repo: https://example.com/custom\n"
        "    hooks:\n"
        "      - id: custom\n"
        "  # OMP-MANAGED-BEGIN\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: gui-naming-linter\n"
        "  # OMP-MANAGED-END\n"
    )
    updateProject(addon)
    text = config.read_text()
    assert "id: custom" in text
    assert "gui-naming-linter" not in text
    assert "id: luacheck" in text and "id: stylua" in text


def testUpdateIsIdempotent(tmp_path):
    addon = _create(tmp_path)
    updateProject(addon)
    snapshot = {p: p.read_bytes() for p in addon.rglob("*") if p.is_file()}
    updateProject(addon)
    assert snapshot == {p: p.read_bytes() for p in snapshot}
    assert set(snapshot) == {p for p in addon.rglob("*") if p.is_file()}


def testUpdateDryRunChangesNothing(tmp_path):
    addon = tmp_path / "Dry"
    addon.mkdir()
    (addon / "Dry.toc").write_text("## Interface: 120001\n")
    updateProject(addon, dryRun=True)
    assert [p.name for p in addon.iterdir()] == ["Dry.toc"]


@pytest.mark.parametrize(
    "interface,flavour",
    [("16001", "forever"), ("11507", "classic"), ("120001", "retail"), ("", "retail")],
)
def testFlavourDetect(interface, flavour):
    assert wowAddon.flavourDetect(interface) == flavour


def testCliCreateWowAddon(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["create", "--project", "CliAddon", "--wow-addon", "--flavour", "forever"])
    assert not (tmp_path / "CliAddon").exists()  # dry-run by default
    main(
        ["create", "--project", "CliAddon", "--wow-addon", "--flavour", "forever", "-y"]
    )
    toc = tmp_path / "CliAddon" / "CliAddon.toc"
    assert wowAddon.tocFieldsRead(toc)["Interface"] == "16001"


def testCliRejectsWowAddonWithUi(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        main(["create", "--project", "X", "--wow-addon", "--ui", "-y"])


@pytest.mark.skipif(shutil.which("lua") is None, reason="lua not installed")
def testStarterLuaCompiles(tmp_path):
    addon = _create(tmp_path)
    subprocess.run(["luac", "-p", str(addon / "MyAddon.lua")], check=True)


def testAddonTestCommandSatisfiesDocCheck(tmp_path):
    addon = tmp_path / "Lint"
    addon.mkdir()
    (addon / "Lint.toc").write_text("## Interface: 120001\n")
    (addon / "README.md").write_text("# Lint\n\nRun `pre-commit run --all-files`.\n")
    updateProject(addon)
    report = AgentCheckValidator(addon).runAll()
    assert "DOC-003" not in {finding.ruleId for finding in report.findings}


def testCreatedAddonReadmeHasTestCommand(tmp_path):
    addon = _create(tmp_path)
    report = AgentCheckValidator(addon).runAll()
    assert "DOC-003" not in {finding.ruleId for finding in report.findings}


def testMigrateWritesAddonProjectYaml(tmp_path):
    from organiseMyProjects.manageProject import migrateProject

    addon = tmp_path / "Old"
    addon.mkdir()
    (addon / "Old.toc").write_text(
        '## Interface: 16001\n## Version: 1.2.3\n## Notes: Says "hi"\n'
    )
    migrateProject(addon)
    text = (addon / "project" / "project.yaml").read_text()
    assert 'role: "wow-addon"' in text
    assert 'flavour: "forever"' in text
    assert 'name: "Old"' in text
    assert 'version: "1.2.3"' in text
    assert "description: \"Says 'hi'\"" in text
