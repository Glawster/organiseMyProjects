from pathlib import Path

from organiseMyProjects import agentCheck, manageProject
from organiseMyProjects.requirementsPromptIndex import promptIndexEnsure


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def testPromptIndexListsFlatRequirementPrompts(tmp_path):
    indexPath = tmp_path / "project/requirements/requirementsIndex.md"
    promptDir = tmp_path / "project/requirements/prompt"
    _write(indexPath, "# Requirements\n\nNext available number: 003\n")
    _write(promptDir / "001-firstFeature.md", "# Prompt\n")
    _write(promptDir / "002a-secondFeature.md", "# Prompt A\n")
    _write(promptDir / "002b-secondFeature.md", "# Prompt B\n")
    _write(promptDir / "promptIndex.md", "# Prompt directory\n")
    _write(promptDir / "notes.md", "# Notes\n")

    promptIndexEnsure(tmp_path)

    text = indexPath.read_text(encoding="utf-8")
    assert "## Prompt index" in text
    assert "prompt/001-firstFeature.md" in text
    assert "prompt/002a-secondFeature.md" in text
    assert "prompt/002b-secondFeature.md" in text
    assert "prompt/promptIndex.md" not in text
    assert "prompt/notes.md" not in text


def testPromptIndexUpdateIsIdempotent(tmp_path):
    indexPath = tmp_path / "project/requirements/requirementsIndex.md"
    promptPath = tmp_path / "project/requirements/prompt/001-firstFeature.md"
    _write(indexPath, "# Requirements\n\nNext available number: 002\n")
    _write(promptPath, "# Prompt\n")

    promptIndexEnsure(tmp_path)
    first = indexPath.read_text(encoding="utf-8")
    promptIndexEnsure(tmp_path)
    second = indexPath.read_text(encoding="utf-8")

    assert first == second


def testAgentCheckFailsWhenPromptIsNotIndexed(tmp_path):
    root = tmp_path
    _write(root / "README.md", "# Project\n")
    _write(root / "AGENTS.md", "# Agents\n")
    _write(
        root / ".github/agent-instructions.md",
        "Read `documentation/requirementsManagement.md`.\n"
        "Read `documentation/repositoryLayout.md` before adding or moving repository content.\n",
    )
    _write(root / "documentation/requirementsManagement.md", "# Requirements management\n")
    _write(root / "documentation/repositoryLayout.md", "# Repository layout\n")
    _write(root / "project/requirements/requirementsIndex.md", "# Requirements\n")
    promptPath = root / "project/requirements/prompt/001-firstFeature.md"
    _write(promptPath, "# Prompt\n")

    report = agentCheck.AgentCheckValidator(root).runAll()

    assert any(f.ruleId == "REQ-006" for f in report.failures)


def testManageProjectUpdateAddsPromptIndex(tmp_path, monkeypatch):
    projectPath = tmp_path / "demo"
    projectPath.mkdir()
    indexPath = projectPath / "project/requirements/requirementsIndex.md"
    promptPath = projectPath / "project/requirements/prompt/001-firstFeature.md"
    _write(indexPath, "# Requirements\n\nNext available number: 002\n")
    _write(promptPath, "# Prompt\n")

    monkeypatch.setattr(manageProject, "_projectIsCanonicalOmp", lambda _path: False)
    manageProject.updateProject(projectPath, dryRun=False)

    assert "prompt/001-firstFeature.md" in indexPath.read_text(encoding="utf-8")
