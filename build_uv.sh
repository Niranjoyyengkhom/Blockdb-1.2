#!/bin/bash

# IEDB Library Build Script for UV and PyPI
#
# This script builds the IEDB library package for distribution via PyPI
# and can be installed using UV or pip.

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IEDB Library Build Script ===${NC}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}UV is not installed. Installing UV...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create and activate virtual environment
echo -e "${YELLOW}Creating virtual environment for build...${NC}"
uv venv .venv-build
source .venv-build/bin/activate

# Install build dependencies
echo -e "${YELLOW}Installing build dependencies...${NC}"
uv pip install build twine wheel setuptools

# Check if README_PYPI.md exists, if so, use it for PyPI
if [ -f README_PYPI.md ]; then
    echo -e "${YELLOW}Using README_PYPI.md for the package...${NC}"
    cp README_PYPI.md README.md.bak
    cp README_PYPI.md README.md
fi

# Build the package
echo -e "${YELLOW}Building the package...${NC}"
python -m build --sdist --wheel

# Restore original README if we made a backup
if [ -f README.md.bak ]; then
    mv README.md.bak README.md
fi

# Check the build with twine
echo -e "${YELLOW}Checking the build with twine...${NC}"
twine check dist/*

echo -e "${GREEN}Build completed successfully!${NC}"
echo ""
echo -e "${YELLOW}To publish to PyPI:${NC}"
echo "twine upload dist/*"
echo ""
echo -e "${YELLOW}To install locally:${NC}"
echo "uv pip install dist/*.whl"
echo ""
echo -e "${YELLOW}To test the package:${NC}"
echo "python -c \"import iedb; print(iedb.__version__)\""