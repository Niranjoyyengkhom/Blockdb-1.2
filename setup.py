"""Setup file for IEDB package.

This file is needed for compatibility with older tools that don't support pyproject.toml.
"""

from setuptools import setup

# This setup.py file is a pass-through to ensure compatibility with tools
# that don't yet support PEP 517/518 (pyproject.toml-based builds).
# All actual configuration is in pyproject.toml

setup(
    name="iedb",
    # Other parameters are automatically read from pyproject.toml
)