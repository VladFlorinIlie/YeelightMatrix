"""Packaging for the YeelightMatrix library.

Build from this directory:

    python -m build          # produces dist/*.whl and dist/*.tar.gz
"""

import os

from setuptools import find_packages, setup

_here = os.path.dirname(__file__)
_readme_path = os.path.join(_here, "..", "README.md")
try:
    with open(_readme_path, encoding="utf-8") as handle:
        long_description = handle.read()
except OSError:
    long_description = "Python library for controlling the Yeelight Cube Matrix."

setup(
    name="YeelightMatrix",
    version="0.2.0",
    description="Python library for controlling the Yeelight Cube Matrix (modular LED cubes).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vlad Florin Ilie",
    url="https://github.com/VladFlorinIlie/YeelightMatrix",
    project_urls={
        "Issues": "https://github.com/VladFlorinIlie/YeelightMatrix/issues",
    },
    license="MIT",
    packages=find_packages(include=["yeelight_matrix*"]),
    python_requires=">=3.10",
    install_requires=[
        "yeelight>=0.7.14",
        "Pillow>=11.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Home Automation",
    ],
)
