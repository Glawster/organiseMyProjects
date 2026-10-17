"""Entry-point logging structure is enforced by the real linter path."""

import ast

import pytest

from organiseMyProjects.guiNamingLinter import loggingSectionsCheck
from organiseMyProjects.runLinter import _lintTarget


def _sourceBuild(start="runStart()", headerLine="line()", summaryLine="line()"):
    return f"""
def main():
    {start or 'pass'}
    logger.value("version", VERSION)
    logger.doing("starting")
    {headerLine or 'pass'}
    processFiles()
    {summaryLine or 'pass'}
    logger.value("processed", count)
    logger.done("finished")
"""


@pytest.mark.parametrize(
    "changes, code",
    [
        ({"start": ""}, "LOG-SEC-001"),
        ({"headerLine": ""}, "LOG-SEC-002"),
        ({"summaryLine": ""}, "LOG-SEC-003"),
    ],
)
def testMissingSectionCall(changes, code):
    findings = loggingSectionsCheck(ast.parse(_sourceBuild(**changes)))
    assert [rule.split(":")[0] for _, rule, _ in findings] == [code]


def testValidSections():
    assert loggingSectionsCheck(ast.parse(_sourceBuild())) == []


def testQualifiedHelpers():
    source = _sourceBuild("logUtils.runStart()", "logUtils.line()", "logUtils.line()")
    assert loggingSectionsCheck(ast.parse(source)) == []


def testTextDoesNotSatisfyCalls():
    source = _sourceBuild('print("runStart()")', 'print("line()")', 'print("line()")')
    assert len(loggingSectionsCheck(ast.parse(source))) == 3


def testLateRunStartIsFlagged():
    source = _sourceBuild("").replace(
        "    processFiles()", "    runStart()\n    processFiles()"
    )
    assert any(
        "LOG-SEC-001" in rule for _, rule, _ in loggingSectionsCheck(ast.parse(source))
    )


def testSeparatorMustPrecedeSummaryCounts():
    source = _sourceBuild(summaryLine="").replace(
        "    logger.done", "    line()\n    logger.done"
    )
    assert any(
        "LOG-SEC-003" in rule for _, rule, _ in loggingSectionsCheck(ast.parse(source))
    )


def testConditionalSummaries():
    source = _sourceBuild().replace(
        '    logger.done("finished")',
        """    if failed:
        logger.done("failed")
        return 1
    else:
        logger.done("finished")""",
    )
    assert loggingSectionsCheck(ast.parse(source)) == []


def testHelpersTestsAndDelegatingDispatcherAreExcluded():
    assert loggingSectionsCheck(ast.parse(_sourceBuild("", "", "")), True) == []
    assert (
        loggingSectionsCheck(
            ast.parse(_sourceBuild("", "", "").replace("def main", "def filesProcess"))
        )
        == []
    )
    assert (
        loggingSectionsCheck(ast.parse("def main():\n    return checkProject()\n"))
        == []
    )


def testRunLinterReportsSectionViolations(tmp_path, capsys):
    target = tmp_path / "main.py"
    target.write_text(_sourceBuild("", "", ""))
    _lintTarget(str(target))
    output = capsys.readouterr().out
    for code in ("LOG-SEC-001", "LOG-SEC-002", "LOG-SEC-003"):
        assert code in output


def testConditionalFailureThenSuccessSummary():
    source = _sourceBuild().replace(
        '    logger.done("finished")',
        """    failed = count == 0
    if failed:
        logger.done("failed")
        return 1
    logger.done("finished")""",
    )
    assert loggingSectionsCheck(ast.parse(source)) == []


def testContextOwningFunctionAndInlineEntryPoint():
    source = _sourceBuild("", "", "").replace(
        "def main():", "def checkProject():\n    setApplication('example')"
    )
    assert len(loggingSectionsCheck(ast.parse(source))) == 3
    source = _sourceBuild("", "", "").replace(
        "def main():", 'if __name__ == "__main__":'
    )
    assert len(loggingSectionsCheck(ast.parse(source))) == 3


def testCallsHiddenInUnusedNestedHelperDoNotCount():
    source = _sourceBuild("", "", "").replace(
        "    processFiles()",
        "    def unused():\n        runStart()\n        line()\n    processFiles()",
    )
    assert len(loggingSectionsCheck(ast.parse(source))) == 3
