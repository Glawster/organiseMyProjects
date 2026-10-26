"""Exercise deterministic SVG generation from the shared Textual theme."""

from pathlib import Path

from organiseMyProjects import styleMockup
from organiseMyProjects.styleMockup import (
    _THEME,
    main,
    styleMockupGenerate,
    styleSheetResolve,
)


def testMockupGeneratesRepresentativeSvg(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(styleMockup, "repositoryRootFind", lambda _start: tmp_path)
    output = styleMockupGenerate()
    svg = output.read_text(encoding="utf-8")
    visible = svg.replace("&#160;", " ")
    assert output == tmp_path / "output" / "myStyles.svg"
    assert svg.startswith("<svg")
    for label in (
        "Shared Textual styles",
        "Normal list item",
        "Search projects",
        "Primary",
        "organiseMyProjects",
        "Success: validation passed",
        "Warning: review required",
        "Error: action failed",
    ):
        assert label in visible


def testMockupCommandWritesFixedPath(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(styleMockup, "repositoryRootFind", lambda _start: tmp_path)
    output = tmp_path / "output" / "myStyles.svg"
    assert main([]) == 0
    assert capsys.readouterr().out.strip() == str(output.resolve())
    assert output.is_file()


def testProjectOwnedStylesheetOverridesOmpTheme(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    override = tmp_path / "styles" / "projectStyles.css"
    override.parent.mkdir()
    override.write_text("Screen { background: #123456; }\n")
    assert styleSheetResolve(tmp_path) == override


def testRootSharedStylesheetDoesNotOverrideOmpTheme(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    managed = tmp_path / "myStyles.css"
    managed.write_text(_THEME.read_text())
    assert styleSheetResolve(tmp_path) == _THEME


def testProjectStylesheetUsesStylesheetDerivedOutputName(tmp_path: Path, monkeypatch):
    override = tmp_path / "styles" / "projectStyles.css"
    override.parent.mkdir()
    override.write_text(_THEME.read_text())
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(styleMockup, "repositoryRootFind", lambda _start: tmp_path)
    assert styleMockupGenerate() == tmp_path / "output" / "projectStyles.svg"
