from setuptools import setup, find_packages

setup(
    name="organiseMyProjects",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pywin32",
        "black",
        "pytest",
        "pre-commit"
    ],
    entry_points={
        "console_scripts": [
            "createProject=organiseMyProjects.createProject:main",
            "runLinter=organiseMyProjects.runLinter:main"
        ]
    },
    author="Andy Wilson (andyw@glawster.com)",
    description="A project scaffolding and GUI linter toolkit for Python projects.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
