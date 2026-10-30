"""Sphinx configuration for Pygame Zero Plus."""

from pathlib import Path
import tomllib

# Read the version from pyproject.toml
ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "pyproject.toml", "rb") as f:
    package_version = tomllib.load(f)["project"]["version"]

# Project information
project = "Pygame Zero Plus"
author = "Michael D'Argenio and Pygame Zero contributors"
copyright = "2015–2026, Daniel Pope, Pygame Zero contributors, and Michael D'Argenio"

version = ".".join(package_version.split(".")[:2])
release = package_version

# General configuration
extensions = [
    "sphinx.ext.autodoc",
]

language = "en"
root_doc = "index"
source_suffix = ".rst"
exclude_patterns = ["_build"]
pygments_style = "sphinx"

# HTML documentation
html_theme = "alabaster"
html_logo = "_static/logo.svg"
html_static_path = ["_static"]
html_show_sourcelink = False

# PDF documentation
latex_documents = [
    (
        "index",
        "PygameZeroPlus.tex",
        "Pygame Zero Plus Documentation",
        author,
        "manual",
    ),
]
