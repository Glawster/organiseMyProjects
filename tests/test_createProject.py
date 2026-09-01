"""
Tests for manageProject.py functionality.
"""

import logging
import os
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from organiseMyProjects.managedContent import (
    DEPLOYMENT_COMMENT,
    POLICY_MANAGED_BLOCK_MERGE,
    POLICY_MANAGED_OVERWRITE,
    POLICY_PROJECT_OWNED_MISSING_ONLY,
    PYTHON_DEPLOYMENT_COMMENT,
)
from organiseMyProjects.manageProject import (
    FILE_OWNERSHIP,
    GITIGNORE_CONTENT,
    MAIN_PY_CONTENT,
    MANAGED_BLOCK_TEMPLATES,
    MANAGED_COPY_TEMPLATES,
    PRECOMMIT_CONTENT,
    PROJECT_TEXT_TEMPLATES,
    PYTEST_INI_CONTENT,
    QT_TEMPLATE_FILES,
    UI_TEMPLATE_FILES,
    VSCODE_SETTINGS_CONTENT,
    _environmentContentBuild,
    _projectIsCanonicalOmp,
    _projectRoleDetect,
    _pyprojectContentBuild,
    createProject,
    updateProject,
)
from organiseMyProjects.manageProject import (
    _fileCopyIfNewer as _copy_if_newer,
)
from organiseMyProjects.manageProject import (
    _managedContentBuild as _build_managed_content,
)
from organiseMyProjects.manageProject import (
    _managedCopyUpdate as _update_managed_copy,
)
from organiseMyProjects.manageProject import (
    _textFileUpdate as _update_text_file,
)
from organiseMyProjects.manageProject import (
    main as createProjectMain,
)
from organiseMyProjects.version import VERSION


def assert_no_gui_scaffolds(projectPath: Path):
    assert not (projectPath / "ui").exists()
    assert not (projectPath / "qt").exists()


class TestCreateProject:
    """Test cases for createProject function."""

    def testCreateProjectBasicStructure(self, temp_dir, sample_project_name):
        """Test that createProject creates the basic directory structure."""
        projectPath = temp_dir / sample_project_name

        # Mock subprocess to avoid git/pre-commit dependencies
        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        # Verify directory structure
        assert projectPath.exists()
        assert (projectPath / sample_project_name).exists()
        assert (projectPath / "tests").exists()
        assert not (projectPath / "src").exists()
        assert not (projectPath / "logs").exists()
        assert (projectPath / ".github").exists()

        # Verify package init files
        assert (projectPath / sample_project_name / "__init__.py").exists()
        assert not (projectPath / "main.py").exists()
        assert_no_gui_scaffolds(projectPath)

    def testCreateProjectCoreFiles(self, temp_dir, sample_project_name):
        """Test that createProject creates core configuration files."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        # Verify core files exist
        assert (projectPath / ".gitignore").exists()
        assert not (projectPath / "requirements.txt").exists()
        assert not (projectPath / "dev-requirements.txt").exists()
        assert not (projectPath / "environment.yml").exists()
        assert (projectPath / f"{sample_project_name}Environment.yml").exists()
        assert (projectPath / "pyproject.toml").exists()
        assert (projectPath / "README.md").exists()
        assert not (projectPath / "main.py").exists()
        assert (projectPath / ".pre-commit-config.yaml").exists()

    def testCreateProjectFileContents(self, temp_dir, sample_project_name):
        """Test that createProject creates files with correct content."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        # Verify file contents
        assert (projectPath / ".gitignore").read_text() == GITIGNORE_CONTENT
        assert (
            projectPath / f"{sample_project_name}Environment.yml"
        ).read_text() == _environmentContentBuild(sample_project_name)
        assert (projectPath / "pyproject.toml").read_text() == _pyprojectContentBuild(
            sample_project_name
        )
        assert (
            f'packages = ["{sample_project_name}"]'
            in (projectPath / "pyproject.toml").read_text()
        )
        assert (
            projectPath / ".pre-commit-config.yaml"
        ).read_text() == PRECOMMIT_CONTENT

        # Verify README content
        readmeContent = (projectPath / "README.md").read_text()
        assert sample_project_name in readmeContent
        assert "Project scaffold created by manageProject.py" in readmeContent

    def testCreateProjectPytestIni(self, temp_dir, sample_project_name):
        """Test that createProject creates pytest.ini with the correct content."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        assert (projectPath / "pytest.ini").exists()
        assert (projectPath / "pytest.ini").read_text() == PYTEST_INI_CONTENT

    def testCreateProjectVscodeSettings(self, temp_dir, sample_project_name):
        """Test that createProject creates .vscode/settings.json with the correct content."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        assert (projectPath / ".vscode" / "settings.json").exists()
        assert (
            projectPath / ".vscode" / "settings.json"
        ).read_text() == VSCODE_SETTINGS_CONTENT

    def testCreateProjectTemplateFiles(self, temp_dir, sample_project_name):
        """Test that only non-UI template files are copied by default."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        # Verify template files are copied
        assert (
            projectPath / sample_project_name / "globalVars.py"
        ).exists(), "globalVars.py should be copied into the project package"
        assert (projectPath / "tests" / "runLinter.py").exists()
        assert (projectPath / "tests" / "guiNamingLinter.py").exists()
        assert_no_gui_scaffolds(projectPath)

        assert not (projectPath / "src").exists()
        assert not (projectPath / "omp").exists()
        assert not (
            projectPath / sample_project_name / "logUtils.py"
        ).exists(), "logUtils.py should NOT be copied into the project package"
        assert not (
            projectPath / "manageProject.py"
        ).exists(), "manageProject.py should NOT be copied to new projects"

    def testCreateProjectUiTemplates(self, temp_dir, sample_project_name):
        """Test that tkinter UI templates are copied only when requested."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath), includeUi=True)

        uiDir = projectPath / sample_project_name / "ui"
        assert (uiDir / "__init__.py").exists()
        assert (uiDir / "styleUtils.py").exists()
        assert (uiDir / "mainMenu.py").exists()
        assert (uiDir / "baseFrame.py").exists()
        assert (uiDir / "frameTemplate.py").exists()
        assert (uiDir / "statusFrame.py").exists()
        assert (projectPath / sample_project_name / "__main__.py").exists()
        assert not (projectPath / "ui").exists()

    def testCreateProjectQtTemplates(self, temp_dir, sample_project_name):
        """Test that Qt templates are copied only when requested."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath), includeQt=True)

        qtDir = projectPath / sample_project_name / "qt"
        assert (qtDir / "__init__.py").exists()
        assert (qtDir / "styleUtils.py").exists()
        assert (qtDir / "mainMenu.py").exists()
        assert (qtDir / "baseFrame.py").exists()
        assert (qtDir / "frameTemplate.py").exists()
        assert (projectPath / sample_project_name / "__main__.py").exists()
        assert not (projectPath / "qt").exists()
        assert (qtDir / "statusFrame.py").exists()

    def testCreateProjectAlreadyExists(self, temp_dir, sample_project_name, caplog):
        """Test behavior when project directory already exists."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()  # Create directory first

        with caplog.at_level(logging.INFO):
            createProject(str(projectPath))

        assert "already exists" in caplog.text

    def testCreateProjectAgentGuidelines(self, temp_dir, sample_project_name):
        """Test that agent guidelines are copied from the .github/ directory."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        agentGuidelines = projectPath / ".github" / "agent-instructions.md"
        copilotGuidelines = projectPath / ".github" / "copilot-instructions.md"
        claudeGuidelines = projectPath / "CLAUDE.md"
        assert agentGuidelines.exists()
        assert len(agentGuidelines.read_text()) > 0
        assert copilotGuidelines.exists()
        assert "agent-instructions.md" in copilotGuidelines.read_text()
        assert "repositoryLayout.md" not in copilotGuidelines.read_text()
        assert claudeGuidelines.exists()
        assert "agent-instructions.md" in claudeGuidelines.read_text()
        assert "repositoryLayout.md" not in claudeGuidelines.read_text()
        assert agentGuidelines.read_text().startswith(DEPLOYMENT_COMMENT)

    def testCreateProjectAgentInstructions(self, temp_dir, sample_project_name):
        """Test that Codex agent instructions are copied to the project root."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        agentFile = projectPath / "AGENTS.md"
        sourceFile = Path(__file__).parent.parent / ".github" / "AGENTS.md"
        assert agentFile.read_text() == _build_managed_content(sourceFile.read_text())
        assert "repositoryLayout.md" not in agentFile.read_text()

    def testCreateProjectRepositoryLayout(self, temp_dir, sample_project_name):
        """Test that the shared repository layout is project documentation."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        layoutFile = projectPath / "documentation" / "repositoryLayout.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "repositoryLayout.md"
        )
        assert layoutFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testCreateProjectRequirementsManagement(self, temp_dir, sample_project_name):
        """Test that the shared requirements guide is project documentation."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        guideFile = projectPath / "documentation" / "requirementsManagement.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "requirementsManagement.md"
        )
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())
        assert (
            "Read `documentation/requirementsManagement.md`."
            in (projectPath / ".github" / "agent-instructions.md").read_text()
        )

    def testCreateProjectTestingProcess(self, temp_dir, sample_project_name):
        """Test that new projects receive the authoritative testing process."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        guideFile = projectPath / "documentation" / "testingProcess.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "testingProcess.md"
        )
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())
        readmeText = (projectPath / "README.md").read_text()
        assert "documentation/repositoryLayout.md" in readmeText
        assert "documentation/requirementsManagement.md" in readmeText
        assert "documentation/testingProcess.md" in readmeText

    def testCreateProjectHowToRelease(self, temp_dir, sample_project_name):
        """Test that the shared release guide is project documentation."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        guideFile = projectPath / "documentation" / "howToRelease.md"
        sourceFile = Path(__file__).parent.parent / "documentation" / "howToRelease.md"
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testCreateProjectAgentPortabilityStructure(self, temp_dir, sample_project_name):
        """Test that project creation scaffolds architecture, currentIncrement, project.yaml, and roadmap."""
        projectPath = temp_dir / sample_project_name

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        assert (projectPath / "documentation" / "architecture.md").exists()
        assert (projectPath / "project" / "currentIncrement.md").exists()
        incrementText = (projectPath / "project" / "currentIncrement.md").read_text()
        assert "## Increment" in incrementText
        assert "## Requirement" in incrementText
        assert "## Verification" in incrementText
        assert "## Next" in incrementText
        assert "## In-Progress Tasks" not in incrementText
        assert "## Handoff & Unresolved Context" not in incrementText
        assert (projectPath / "project" / "project.yaml").exists()
        assert (projectPath / "project" / "roadmap.md").exists()
        assert (projectPath / "project" / "requirements" / "folderIndex.md").exists()
        assert not (projectPath / "project" / "requirements" / "README.md").exists()
        assert (
            projectPath / "project" / "requirements" / "templates" / "requirement.md"
        ).exists()
        requirementText = (
            projectPath / "project" / "requirements" / "templates" / "requirement.md"
        ).read_text()
        assert "## Traceability" not in requirementText
        assert (projectPath / "project" / "adr" / "folderIndex.md").exists()
        assert not (projectPath / "project" / "adr" / "README.md").exists()
        assert (projectPath / "project" / "adr" / "templates" / "adr.md").exists()


class TestProjectRoleDetection:
    """Classify established Python layouts without executing their metadata."""

    def testSetupPyConsoleScriptsDetectPackagedCli(self, tmp_path):
        (tmp_path / "setup.py").write_text(
            'setup(entry_points={"console_scripts": ["tool=package.cli:main"]})\n'
        )
        (tmp_path / "package").mkdir()
        (tmp_path / "package" / "__init__.py").write_text("")

        assert _projectRoleDetect(tmp_path) == "packaged-cli"

    def testSetupPyFlatPackageDetectsLibrary(self, tmp_path):
        (tmp_path / "setup.py").write_text("setup(packages=find_packages())\n")
        (tmp_path / "package").mkdir()
        (tmp_path / "package" / "__init__.py").write_text("")

        assert _projectRoleDetect(tmp_path) == "library"

    def testPep621FlatPackageDetectsLibrary(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example-package"\n'
        )
        (tmp_path / "package").mkdir()
        (tmp_path / "package" / "__init__.py").write_text("")

        assert _projectRoleDetect(tmp_path) == "library"

    def testOmpRepositoryDetectsPackagedCli(self):
        repositoryRoot = Path(__file__).parent.parent

        assert _projectRoleDetect(repositoryRoot) == "packaged-cli"

    def testCanonicalOmpRepositoryDetection(self):
        repositoryRoot = Path(__file__).parent.parent

        assert _projectIsCanonicalOmp(repositoryRoot)


class TestUpdateProject:
    """Test cases for updateProject function."""

    def testUpdateProjectExisting(self, temp_dir, sample_project_name):
        """Test updating an existing project without scaffold growth."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        # Verify only managed metadata folders are created by default
        assert (projectPath / ".github").exists()
        assert not (projectPath / "src").exists()
        # Managed test helper files are still deployed under tests/
        assert (projectPath / "tests").exists()
        assert not (projectPath / "logs").exists()
        assert_no_gui_scaffolds(projectPath)

    def testUpdateCanonicalOmpRepositoryIsNoOp(self, tmp_path):
        """OMP owns templates and must never deploy its scaffolds over itself."""
        projectPath = tmp_path / "organiseMyProjects"
        packagePath = projectPath / "organiseMyProjects"
        packagePath.mkdir(parents=True)
        (packagePath / "manageProject.py").write_text("# canonical source\n")
        (projectPath / "syncAgentInstructions.py").write_text("# sync utility\n")
        (projectPath / "pyproject.toml").write_text(
            '[project]\nname = "organiseMyProjects"\n'
        )

        updateProject(projectPath)

        assert (packagePath / "manageProject.py").read_text() == "# canonical source\n"
        assert not (projectPath / "pytest.ini").exists()
        assert not (projectPath / ".vscode").exists()
        assert not (projectPath / "tests").exists()

    def testUpdateProjectNonexistent(self, temp_dir, sample_project_name, caplog):
        """Test behavior when trying to update non-existent project."""
        projectPath = temp_dir / sample_project_name

        with caplog.at_level(logging.INFO):
            updateProject(str(projectPath))

        assert "does not exist" in caplog.text

    def testUpdateProjectPytestIni(self, temp_dir, sample_project_name):
        """Test that updateProject creates/updates pytest.ini with the correct content."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / "pytest.ini").exists()
        assert (projectPath / "pytest.ini").read_text() == PYTEST_INI_CONTENT

    def testUpdateProjectVscodeSettings(self, temp_dir, sample_project_name):
        """Test that updateProject creates/updates .vscode/settings.json with the correct content."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / ".vscode" / "settings.json").exists()
        assert (
            projectPath / ".vscode" / "settings.json"
        ).read_text() == VSCODE_SETTINGS_CONTENT

    def testUpdateProjectAddsAgentInstructions(self, temp_dir, sample_project_name):
        """Test that updateProject adds managed Codex agent instructions."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        updateProject(str(projectPath))

        agentFile = projectPath / "AGENTS.md"
        sourceFile = Path(__file__).parent.parent / ".github" / "AGENTS.md"
        assert agentFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testUpdateProjectAddsRepositoryLayout(self, temp_dir, sample_project_name):
        """Test that updateProject adds the managed repository layout."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        updateProject(str(projectPath))

        layoutFile = projectPath / "documentation" / "repositoryLayout.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "repositoryLayout.md"
        )
        assert layoutFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testUpdateProjectAddsRequirementsManagement(
        self, temp_dir, sample_project_name
    ):
        """Test that updateProject adds the managed requirements guide."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        updateProject(str(projectPath))

        guideFile = projectPath / "documentation" / "requirementsManagement.md"
        sourceFile = (
            Path(__file__).parent.parent / "documentation" / "requirementsManagement.md"
        )
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testUpdateProjectMigratesUnambiguousLegacyNames(
        self, temp_dir, sample_project_name
    ):
        """Migrate legacy OMP names without overwriting arbitrary targets."""
        projectPath = temp_dir / sample_project_name
        testsPath = projectPath / "tests"
        featuresPath = projectPath / "project" / "requirements" / "features"
        promptsPath = projectPath / "project" / "requirements" / "prompt"
        testsPath.mkdir(parents=True)
        featuresPath.mkdir(parents=True)
        promptsPath.mkdir(parents=True)
        (testsPath / "test_FooBar.py").write_text("def test_example(): pass\n")
        (featuresPath / "007-roleAssessment.md").write_text("# 007: Role assessment\n")
        (promptsPath / "007-roleAssessment.prompt.md").write_text("# Prompt\n")
        requirementsIndex = projectPath / "project" / "requirements" / "README.md"
        requirementsIndex.write_text(
            "# Requirements\n\n[Prompt](prompt/007-roleAssessment.prompt.md)\n"
        )

        updateProject(str(projectPath))

        assert (testsPath / "test_fooBar.py").exists()
        assert not (testsPath / "test_FooBar.py").exists()
        assert (promptsPath / "007-roleAssessment.md").exists()
        assert "prompt/007-roleAssessment.md" in requirementsIndex.read_text()

    def testUpdateProjectAddsHowToRelease(self, temp_dir, sample_project_name):
        """Test that updateProject adds the managed release process guide."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        updateProject(str(projectPath))

        guideFile = projectPath / "documentation" / "howToRelease.md"
        sourceFile = Path(__file__).parent.parent / "documentation" / "howToRelease.md"
        assert guideFile.read_text() == _build_managed_content(sourceFile.read_text())

    def testUpdateProjectPreservesExistingPytestIni(
        self, temp_dir, sample_project_name
    ):
        """Project-owned pytest configuration is preserved except the managed block."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        (projectPath / "pytest.ini").write_text("[pytest]\ntestpaths = custom\n")

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        text = (projectPath / "pytest.ini").read_text()
        assert "testpaths = custom" in text
        assert "python_files = test_[a-z]*.py" in text
        assert "OMP-MANAGED-BEGIN" in text

    def testUpdateProjectPreservesExistingVscodeSettings(
        self, temp_dir, sample_project_name
    ):
        """Project-owned editor configuration is preserved except the managed block."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        (projectPath / ".vscode").mkdir()
        (projectPath / ".vscode" / "settings.json").write_text('{"old": true}')

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        text = (projectPath / ".vscode" / "settings.json").read_text()
        assert '"old": true' in text
        assert "python.testing.pytestEnabled" in text
        assert "OMP-MANAGED-BEGIN" in text

    def testUpdateProjectPreservesExistingUiTemplates(
        self, temp_dir, sample_project_name
    ):
        """Test that updateProject does not modify project-owned tkinter scaffolds."""
        projectPath = temp_dir / sample_project_name
        (projectPath / "ui").mkdir(parents=True)
        customMainMenu = "print('custom ui')\n"
        (projectPath / "ui" / "mainMenu.py").write_text(customMainMenu)

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / "ui" / "mainMenu.py").read_text() == customMainMenu
        assert not (projectPath / "ui" / "statusFrame.py").exists()

    def testUpdateProjectPreservesExistingMainPy(self, temp_dir, sample_project_name):
        """Test that updateProject does not overwrite project-owned main.py code."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        customMain = "print('custom main')\n"
        (projectPath / "main.py").write_text(customMain)

        with patch("organiseMyProjects.manageProject.subprocess.run"):
            updateProject(str(projectPath))

        assert (projectPath / "main.py").read_text() == customMain


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def testBuildManagedPythonContentPreservesShebang(self):
        """Python deployment comments must follow the interpreter directive."""
        source = '#!/usr/bin/env python3\n"""CLI entry point."""\n'

        content = _build_managed_content(source, suffix=".py")

        assert content == (
            "#!/usr/bin/env python3\n"
            + PYTHON_DEPLOYMENT_COMMENT
            + '"""CLI entry point."""\n'
        )
        compile(content, "runLinter.py", "exec")

    def testBuildManagedContentCollapsesExistingReleaseMarkers(self):
        """Generated output contains one marker even when its source has several."""
        source = (
            "<!-- deployed from Glawster/organiseMyProjects release 0.5 "
            "-- do not edit directly -->\n"
            "<!-- deployed from Glawster/organiseMyProjects release 0.4 "
            "-- do not edit directly -->\n"
            "# Agent Instructions\n"
        )

        content = _build_managed_content(source)

        assert content == DEPLOYMENT_COMMENT + "# Agent Instructions\n"
        assert content.count("organiseMyProjects release") == 1

    def testCopyIfNewerNewFile(self, temp_dir):
        """Test copying when destination doesn't exist."""
        src = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"

        src.write_text("test content")

        _copy_if_newer(src, dest)

        assert dest.exists()
        assert dest.read_text() == "test content"

    def testCopyIfNewerOlderDest(self, temp_dir):
        """Test copying when source is newer than destination."""
        import time

        src = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"

        # Create dest first (older)
        dest.write_text("old content")

        # Wait a bit to ensure different modification times
        time.sleep(0.1)

        # Create src after (newer)
        src.write_text("new content")

        _copy_if_newer(src, dest)

        assert dest.read_text() == "new content"

    def testUpdateTextFileNew(self, temp_dir):
        """Test updating text file when it doesn't exist."""
        dest = temp_dir / "test.txt"
        content = "test content"

        _update_text_file(dest, content)

        assert dest.exists()
        assert dest.read_text() == content

    def testUpdateTextFileSameContent(self, temp_dir):
        """Test updating text file when content is the same."""
        dest = temp_dir / "test.txt"
        content = "test content"

        dest.write_text(content)
        originalMtime = dest.stat().st_mtime

        _update_text_file(dest, content)

        # File should not be modified if content is the same
        assert dest.stat().st_mtime == originalMtime

    def testUpdateTextFileDifferentContent(self, temp_dir):
        """Test updating text file when content is different."""
        dest = temp_dir / "test.txt"
        oldContent = "old content"
        newContent = "new content"

        dest.write_text(oldContent)

        _update_text_file(dest, newContent)

        assert dest.read_text() == newContent


class TestUpdateHelpers:
    """Test helper behavior used during project updates."""

    def testManagedCopyIgnoresReleaseMarkerOnlyChange(self, temp_dir):
        """Do not rewrite a managed document when only its OMP release differs."""
        src = temp_dir / "source.md"
        dest = temp_dir / "destination.md"
        src.write_text("# Managed guide\n\nStable content.\n")
        oldContent = (
            "<!-- deployed from Glawster/organiseMyProjects release 0.4 "
            "-- do not edit directly -->\n# Managed guide\n\nStable content.\n"
        )
        dest.write_text(oldContent)

        _update_managed_copy(src, dest)

        assert dest.read_text() == oldContent

    def testManagedPythonCopyIgnoresReleaseMarkerOnlyChange(self, temp_dir):
        """Compare Python content beneath both its shebang and release marker."""
        src = temp_dir / "source.py"
        dest = temp_dir / "destination.py"
        body = '#!/usr/bin/env python3\nprint("stable")\n'
        src.write_text(body)
        oldContent = (
            "#!/usr/bin/env python3\n"
            "# deployed from Glawster/organiseMyProjects release 0.4 "
            "-- do not edit directly\n"
            'print("stable")\n'
        )
        dest.write_text(oldContent)

        _update_managed_copy(src, dest)

        assert dest.read_text() == oldContent

    def testManagedCopyUpdatesSubstantiveContent(self, temp_dir):
        """A release marker must not hide an actual managed-content change."""
        src = temp_dir / "source.md"
        dest = temp_dir / "destination.md"
        src.write_text("# Managed guide\n\nNew content.\n")
        dest.write_text(
            "<!-- deployed from Glawster/organiseMyProjects release 0.4 "
            "-- do not edit directly -->\n# Managed guide\n\nOld content.\n"
        )

        _update_managed_copy(src, dest)

        assert dest.read_text() == _build_managed_content(src.read_text())

    def testManagedCopyCollapsesDuplicateReleaseMarkers(self, temp_dir):
        """Repair duplicate headers even when the managed body is unchanged."""
        src = temp_dir / "source.md"
        dest = temp_dir / "destination.md"
        src.write_text("# Managed guide\n")
        dest.write_text(
            "<!-- deployed from Glawster/organiseMyProjects release 0.5 "
            "-- do not edit directly -->\n"
            "<!-- deployed from Glawster/organiseMyProjects release 0.4 "
            "-- do not edit directly -->\n"
            "# Managed guide\n"
        )

        _update_managed_copy(src, dest)

        assert dest.read_text() == DEPLOYMENT_COMMENT + "# Managed guide\n"

    def testCopyIfNewerOverwritesWithoutBackup(self, temp_dir):
        """Test that _copy_if_newer updates in place without creating backup files."""
        import time

        src = temp_dir / "source.py"
        dest = temp_dir / "dest.py"

        dest.write_text("old content")
        time.sleep(0.05)
        src.write_text("new content")

        _copy_if_newer(src, dest)

        assert dest.read_text() == "new content"
        assert list(temp_dir.glob("dest.*.py")) == []

    def testUpdateTextFileOverwritesWithoutBackup(self, temp_dir):
        """Test that _update_text_file updates in place without creating backup files."""
        dest = temp_dir / "config.txt"
        dest.write_text("old")

        _update_text_file(dest, "new content")

        assert dest.read_text() == "new content"
        assert list(temp_dir.glob("config.*.txt")) == []

    def testUpdateTextFileNoBackupWhenSameContent(self, temp_dir):
        """Test that _update_text_file does not create backup-like files when unchanged."""
        dest = temp_dir / "config.txt"
        dest.write_text("same content")

        _update_text_file(dest, "same content")

        assert list(temp_dir.glob("config.*.txt")) == []


class TestDryRun:
    """Test that dry-run mode logs actions without writing any files."""

    def testCreateProjectDryRunNoFilesCreated(self, temp_dir, sample_project_name):
        """Test that createProject in dry-run mode does not create the project directory."""
        projectPath = temp_dir / sample_project_name

        createProject(str(projectPath), dryRun=True)

        assert (
            not projectPath.exists()
        ), "Project directory must not be created in dry-run mode"

    def testCreateProjectDryRunLogsActions(self, temp_dir, sample_project_name, caplog):
        """Test that createProject in dry-run mode logs the actions it would take."""
        projectPath = temp_dir / sample_project_name

        with caplog.at_level(logging.INFO):
            createProject(str(projectPath), dryRun=True)

        assert "creating project" in caplog.text
        assert "creating directories" in caplog.text
        assert "writing core files" in caplog.text

    def testUpdateProjectDryRunNoFilesModified(self, temp_dir, sample_project_name):
        """Test that updateProject in dry-run mode does not modify existing files."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()
        (projectPath / "src").mkdir()
        sentinel = projectPath / "src" / "globalVars.py"
        sentinel.write_text("original content")

        updateProject(str(projectPath), dryRun=True)

        assert (
            sentinel.read_text() == "original content"
        ), "File must not be modified in dry-run mode"

    def testUpdateProjectDryRunLogsActions(self, temp_dir, sample_project_name, caplog):
        """Test that updateProject in dry-run mode logs the actions it would take."""
        projectPath = temp_dir / sample_project_name
        projectPath.mkdir()

        with caplog.at_level(logging.INFO):
            updateProject(str(projectPath), dryRun=True)

        assert "updating project" in caplog.text
        assert "would create" in caplog.text
        assert "update simulation complete: no changes were applied" in caplog.text
        assert "created " not in caplog.text.replace("would create", "")

    def testCopyIfNewerDryRunNoWrite(self, temp_dir):
        """Test that _copy_if_newer in dry-run mode does not write the destination file."""
        src = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"
        src.write_text("new content")

        _copy_if_newer(src, dest, dryRun=True)

        assert not dest.exists(), "Destination file must not be created in dry-run mode"

    def testUpdateTextFileDryRunNoWrite(self, temp_dir):
        """Test that _update_text_file in dry-run mode does not write the file."""
        dest = temp_dir / "output.txt"

        _update_text_file(dest, "some content", dryRun=True)

        assert not dest.exists(), "File must not be created in dry-run mode"


class TestCliFlags:
    """Test CLI flag handling for createProject."""

    def testMainLogsOmpVersion(self):
        """Test that manageProject records the running OMP release."""
        with patch("organiseMyProjects.manageProject.getLogger") as getLogger:
            with patch("organiseMyProjects.manageProject.createProject"):
                with patch("sys.argv", ["manageProject.py", "demo"]):
                    createProjectMain()

        getLogger.return_value.value.assert_called_once_with("OMP version", VERSION)

    def testMainPassesUiAndQtFlagsToCreateProject(self):
        with patch("organiseMyProjects.manageProject.createProject") as mockCreate:
            with patch(
                "sys.argv",
                ["manageProject.py", "demo", "--ui", "-qt", "--confirm"],
            ):
                createProjectMain()

        mockCreate.assert_called_once_with(
            "demo",
            dryRun=False,
            includeUi=True,
            includeQt=True,
        )

    def testMainPassesQtFlagToUpdateProject(self):
        with patch("organiseMyProjects.manageProject.updateProject") as mockUpdate:
            with patch(
                "sys.argv",
                ["manageProject.py", "--update", "-qt", "--confirm"],
            ):
                createProjectMain()

        mockUpdate.assert_called_once_with(
            Path.cwd(),
            dryRun=False,
            includeUi=False,
            includeQt=True,
        )

    def testMainPassesLegacyProjectFlagToCreateProject(self):
        with patch("organiseMyProjects.manageProject.createProject") as mockCreate:
            with patch(
                "sys.argv",
                ["manageProject.py", "--project", "demo", "--confirm"],
            ):
                createProjectMain()

        mockCreate.assert_called_once_with(
            "demo",
            dryRun=False,
            includeUi=False,
            includeQt=False,
        )

    def testMainPassesLegacyProjectFlagToUpdateProject(self):
        with patch("organiseMyProjects.manageProject.updateProject") as mockUpdate:
            with patch(
                "sys.argv",
                ["manageProject.py", "--update", "--project", "demo", "--confirm"],
            ):
                createProjectMain()

        mockUpdate.assert_called_once_with(
            "demo",
            dryRun=False,
            includeUi=False,
            includeQt=False,
        )

    def testMainPassesSyncFlagsToSyncModule(self):
        capturedArgv = []

        def fakeSyncMain():
            capturedArgv.extend(sys.argv)

        fakeSyncModule = types.SimpleNamespace(main=fakeSyncMain)

        with patch(
            "organiseMyProjects.manageProject._loadSyncModule",
            return_value=fakeSyncModule,
        ):
            with patch(
                "sys.argv",
                [
                    "manageProject.py",
                    "--sync",
                    "--confirm",
                    "--merge",
                    "--repo",
                    "Glawster/demo",
                    "--token",
                    "token123",
                    "--verbose",
                ],
            ):
                createProjectMain()

        assert capturedArgv == [
            "syncAgentInstructions.py",
            "--confirm",
            "--merge",
            "--repo",
            "Glawster/demo",
            "--token",
            "token123",
            "--verbose",
        ]


class TestOwnershipPolicy:
    """Every deployed file has exactly one ownership policy."""

    def testEveryDeclaredPathHasAKnownPolicy(self):
        allowed = {
            POLICY_MANAGED_OVERWRITE,
            POLICY_MANAGED_BLOCK_MERGE,
            POLICY_PROJECT_OWNED_MISSING_ONLY,
        }
        assert FILE_OWNERSHIP
        assert set(FILE_OWNERSHIP.values()) <= allowed

    def testTemplateListsAreCoveredByOwnership(self):
        declared = set(FILE_OWNERSHIP)
        for _src, destRel in MANAGED_COPY_TEMPLATES:
            assert destRel.as_posix() in declared
        for destRel, _content, _block, _prefix in MANAGED_BLOCK_TEMPLATES:
            assert destRel.as_posix() in declared
        for destRel, _content in PROJECT_TEXT_TEMPLATES:
            assert destRel.as_posix() in declared
        for name in UI_TEMPLATE_FILES:
            assert f"ui/{name}" in declared
        for name in QT_TEMPLATE_FILES:
            assert f"qt/{name}" in declared

    def testGeneratedMainImportsOrganiseMyProjectsLogging(self):
        assert (
            "from organiseMyProjects.logUtils import getLogger, setApplication"
            in MAIN_PY_CONTENT
        )


class TestPackagedCliUpdate:
    """Established packaged CLIs keep their layout across confirmed updates."""

    def _packagedCliFixture(self, temp_dir: Path) -> Path:
        projectPath = temp_dir / "packagedCli"
        package = projectPath / "packagedCli"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        (package / "cli.py").write_text("def main():\n    return 0\n")
        (projectPath / "pyproject.toml").write_text(
            '[project]\nname = "packagedCli"\n\n'
            '[project.scripts]\ntool = "packagedCli.cli:main"\n'
        )
        (projectPath / "pytest.ini").write_text(
            "[pytest]\ntestpaths = tests\npython_files = test_*.py\n"
        )
        testsPath = projectPath / "tests"
        testsPath.mkdir()
        (testsPath / "test_cli.py").write_text("def test_ok():\n    assert True\n")
        return projectPath

    def testPackagedCliUpdateDoesNotAddApplicationScaffold(self, temp_dir):
        projectPath = self._packagedCliFixture(temp_dir)
        originalPyproject = (projectPath / "pyproject.toml").read_text()

        updateProject(str(projectPath))
        updateProject(str(projectPath))

        assert not (projectPath / "main.py").exists()
        assert not (projectPath / "src").exists()
        assert_no_gui_scaffolds(projectPath)
        assert (projectPath / "pyproject.toml").read_text() == originalPyproject
        assert not (projectPath / "omp").exists()
        assert (
            "python_files = test_[a-z]*.py" in (projectPath / "pytest.ini").read_text()
        )
        assert "[project.scripts]" in originalPyproject

    def testSecondUpdateIsIdempotentForManagedRuntime(self, temp_dir):
        projectPath = self._packagedCliFixture(temp_dir)
        updateProject(str(projectPath))
        firstPytest = (projectPath / "pytest.ini").read_text()
        firstAgent = (projectPath / ".github" / "agent-instructions.md").read_text()

        updateProject(str(projectPath))

        assert (projectPath / "pytest.ini").read_text() == firstPytest
        assert (projectPath / ".github" / "agent-instructions.md").read_text() == (
            firstAgent
        )
        assert not (projectPath / "omp").exists()


class TestImportAndPytestEvidence:
    """Production-path checks for import safety and generated pytest config."""

    def testCommandModulesImportWithoutCreatingLogFiles(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["PYTHONPATH"] = str(Path(__file__).parent.parent)
        script = (
            "from organiseMyProjects.manageProject import createProject\n"
            "from organiseMyProjects import runLinter\n"
            "from organiseMyProjects.guiNamingLinter import lintFile\n"
            "print('imported')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            env=env,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert "imported" in result.stdout
        stateDir = home / ".local" / "state"
        logFiles = list(stateDir.rglob("*.log")) if stateDir.exists() else []
        assert logFiles == []

    def testGeneratedPytestIniIsLoadedByPytest(self, temp_dir, sample_project_name):
        projectPath = temp_dir / sample_project_name
        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(projectPath))

        testsPath = projectPath / "tests"
        (testsPath / "test_collected.py").write_text(
            "def test_ok():\n    assert True\n"
        )
        (testsPath / "test_Skipped.py").write_text(
            "def test_should_not_collect():\n    assert True\n"
        )

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=projectPath,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "test_collected.py" in result.stdout
        assert "test_Skipped.py" not in result.stdout
        assert "test_should_not_collect" not in result.stdout
