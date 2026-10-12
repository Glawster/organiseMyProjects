"""Regression tests for OMP 0.8 linter behaviour and migration."""

from pathlib import Path
from unittest.mock import patch

from organiseMyProjects.guiNamingLinter import fileCheck
from organiseMyProjects.linter08 import LOGGING_CASE_WHITELIST
from organiseMyProjects.manageProject import createProject, updateProject
from organiseMyProjects import runLinter


class TestLinter08Naming:
    def testDigitBearingDomainActionNamesAreAccepted(self, temp_dir):
        source = temp_dir / "media.py"
        source.write_text(
            "def _mp4BoxIterate():\n"
            "    return None\n\n\n"
            "def _mp4MvhdCreationRead():\n"
            "    return None\n",
            encoding="utf-8",
        )

        names = {item[0] for item in fileCheck(str(source))}
        assert "_mp4BoxIterate" not in names
        assert "_mp4MvhdCreationRead" not in names

    def testTextualActionAndEventHooksAreAccepted(self, temp_dir):
        source = temp_dir / "screen.py"
        source.write_text(
            "from textual.app import App\n\n\n"
            "class MailApp(App):\n"
            "    def action_policy_positive(self):\n"
            "        pass\n\n"
            "    def action_sender_edit(self):\n"
            "        pass\n\n"
            "    def on_button_pressed(self, event):\n"
            "        pass\n\n"
            "    def on_action_needed_navigate(self, event):\n"
            "        pass\n",
            encoding="utf-8",
        )

        names = {item[0] for item in fileCheck(str(source))}
        assert names.isdisjoint(
            {
                "action_policy_positive",
                "action_sender_edit",
                "on_button_pressed",
                "on_action_needed_navigate",
            }
        )

    def testSnakeCaseMethodOutsideTextualStillFails(self, temp_dir):
        source = temp_dir / "service.py"
        source.write_text(
            "class Service:\n"
            "    def action_policy_positive(self):\n"
            "        pass\n",
            encoding="utf-8",
        )

        assert any(
            item[0] == "action_policy_positive" and "Method name" in item[1]
            for item in fileCheck(str(source))
        )

    def testApprovedLoggingTokensPreserveCase(self, temp_dir):
        source = temp_dir / "logging.py"
        source.write_text(
            "logger.info('using GoPro and SQLite metadata')\n"
            "logger.warning('Grok check unavailable')\n"
            "logger.error('Could not read TVDB metadata')\n",
            encoding="utf-8",
        )

        caseFindings = [
            item for item in fileCheck(str(source)) if item[1].startswith("Logging (")
        ]
        assert caseFindings == []

    def testUnapprovedMixedCaseLoggingTokenStillFails(self, temp_dir):
        source = temp_dir / "logging.py"
        source.write_text(
            "logger.info('using UnexpectedBrand metadata')\n",
            encoding="utf-8",
        )

        assert any(item[1] == "Logging (info)" for item in fileCheck(str(source)))
        assert runLinter._violationAllowed(
            "using UnexpectedBrand metadata", "Logging (info)"
        ) is False

    def testLoggingWhitelistIsExplicit(self):
        assert LOGGING_CASE_WHITELIST == {
            "DJI",
            "Firefox",
            "GoPro",
            "Grok",
            "MCM",
            "SQLite",
            "TVDB",
            "X.ai",
        }


class TestCentralisedLinter:
    def testCreateDoesNotCopyLinterImplementations(self, temp_dir):
        project = temp_dir / "exampleProject"
        with patch("organiseMyProjects.manageProject.subprocess.run"):
            createProject(str(project))

        assert not (project / "tests" / "runLinter.py").exists()
        assert not (project / "tests" / "guiNamingLinter.py").exists()
        assert (project / "documentation" / "linter.md").is_file()
        precommit = (project / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        assert "entry: runLinter" in precommit

    def testUpdateRemovesUnmodifiedLegacyCopies(self, temp_dir):
        project = temp_dir / "legacyProject"
        project.mkdir()
        tests = project / "tests"
        tests.mkdir()
        package = Path(__file__).parent.parent / "organiseMyProjects"
        for name in ("runLinter.py", "guiNamingLinter.py"):
            (tests / name).write_text(
                (package / name).read_text(encoding="utf-8"), encoding="utf-8"
            )

        updateProject(str(project))

        assert not (tests / "runLinter.py").exists()
        assert not (tests / "guiNamingLinter.py").exists()

    def testUpdatePreservesModifiedLegacyCopy(self, temp_dir):
        project = temp_dir / "modifiedProject"
        tests = project / "tests"
        tests.mkdir(parents=True)
        local = tests / "runLinter.py"
        local.write_text("# locally maintained linter\n", encoding="utf-8")

        updateProject(str(project))

        assert local.read_text(encoding="utf-8") == "# locally maintained linter\n"

    def testDryRunReportsButDoesNotRemoveLegacyCopy(self, temp_dir):
        project = temp_dir / "dryRunProject"
        tests = project / "tests"
        tests.mkdir(parents=True)
        package = Path(__file__).parent.parent / "organiseMyProjects"
        local = tests / "runLinter.py"
        local.write_text(
            (package / "runLinter.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        updateProject(str(project), dryRun=True)

        assert local.exists()

    def testMigrationIsIdempotent(self, temp_dir):
        project = temp_dir / "idempotentProject"
        tests = project / "tests"
        tests.mkdir(parents=True)
        package = Path(__file__).parent.parent / "organiseMyProjects"
        local = tests / "guiNamingLinter.py"
        local.write_text(
            (package / "guiNamingLinter.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        updateProject(str(project))
        updateProject(str(project))

        assert not local.exists()
