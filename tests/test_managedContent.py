from organiseMyProjects.managedContent import managedBlockMergeText


def testManagedBlockAdoptsLegacyScalarSetting():
    existing = """[pytest]
testpaths = tests
pythonpath = .
python_files = test*.py
python_functions = test*
python_classes = Test*
addopts =
    -v
"""

    merged = managedBlockMergeText(
        existing,
        "python_files = test_[a-z]*.py",
        "#",
    )

    assert "python_files = test*.py" not in merged
    assert merged.count("python_files = test_[a-z]*.py") == 1
    assert "testpaths = tests" in merged
    assert "pythonpath = ." in merged
    assert "python_functions = test*" in merged
    assert "python_classes = Test*" in merged
    assert "-v" in merged


def testManagedBlockRemovesDuplicateOutsideExistingBlock():
    existing = """[pytest]
python_files = test*.py
# OMP-MANAGED-BEGIN
python_files = test_old*.py
# OMP-MANAGED-END
python_functions = test*
"""

    merged = managedBlockMergeText(
        existing,
        "python_files = test_[a-z]*.py",
        "#",
    )

    assert "python_files = test*.py" not in merged
    assert "python_files = test_old*.py" not in merged
    assert merged.count("python_files = test_[a-z]*.py") == 1
    assert "python_functions = test*" in merged


def testManagedJsonBlockAdoptsLegacySettings():
    existing = """{
   "editor.formatOnSave": true,
   "python.testing.pytestEnabled": false,
   "python.testing.unittestEnabled": true,
   "python.testing.nosetestsEnabled": true,
   "python.testing.pytestArgs": [
      "tests",
      "--legacy"
   ],
   "files.trimTrailingWhitespace": true
}
"""
    block = """   "python.testing.pytestEnabled": true,
   "python.testing.unittestEnabled": false,
   "python.testing.nosetestsEnabled": false,
   "python.testing.pytestArgs": [
      "tests",
      "--override-ini=python_files=test_[a-z]*.py"
   ]"""

    merged = managedBlockMergeText(
        existing,
        block,
        "//",
        jsonStyle=True,
    )

    assert merged.count('"python.testing.pytestEnabled"') == 1
    assert merged.count('"python.testing.unittestEnabled"') == 1
    assert merged.count('"python.testing.nosetestsEnabled"') == 1
    assert merged.count('"python.testing.pytestArgs"') == 1
    assert "--legacy" not in merged
    assert "--override-ini=python_files=test_[a-z]*.py" in merged
    assert '"editor.formatOnSave": true' in merged
    assert '"files.trimTrailingWhitespace": true' in merged


def testManagedJsonBlockRemovesDuplicatesOutsideExistingBlock():
    existing = """{
   "python.testing.pytestEnabled": false,
   // OMP-MANAGED-BEGIN
   "python.testing.pytestEnabled": false,
   "python.testing.pytestArgs": ["old"]
   // OMP-MANAGED-END
   "editor.wordWrap": "on"
}
"""
    block = """   "python.testing.pytestEnabled": true,
   "python.testing.pytestArgs": [
      "tests"
   ]"""

    merged = managedBlockMergeText(
        existing,
        block,
        "//",
        jsonStyle=True,
    )

    assert merged.count('"python.testing.pytestEnabled"') == 1
    assert merged.count('"python.testing.pytestArgs"') == 1
    assert '["old"]' not in merged
    assert '"editor.wordWrap": "on"' in merged
