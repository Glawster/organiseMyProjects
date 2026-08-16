from setuptools import setup, find_packages

setup(
    name="organiseMyProjects",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    install_requires=[
        'pywin32; sys_platform == "win32"',
        "black",
        "pytest",
        "pre-commit",
        "ruff",
    ],
    entry_points={
        "console_scripts": [
            "manageProject=organiseMyProjects.manageProject:main",
            "createProject=organiseMyProjects.manageProject:main",
            "updateProject=organiseMyProjects.manageProject:main",
            "runLinter=organiseMyProjects.runLinter:main",
            "fixMarkup=organiseMyProjects.fixMarkup:main",
            "agentCheck=organiseMyProjects.agentCheck:main",
        ]
    },
    author="Andy Wilson (andyw@glawster.com)",
    description="A project scaffolding and GUI linter toolkit for Python projects.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
