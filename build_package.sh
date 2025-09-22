#!/usr/bin/env bash

# Build script for IEDB package
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building IEDB package...${NC}"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}UV is not installed. Please install UV first:${NC}"
    echo "curl -sSf https://astral.sh/uv/install.sh | bash"
    exit 1
fi

# Install build dependencies if needed
echo -e "${YELLOW}Installing build dependencies...${NC}"
uv pip install build twine hatchling

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf dist/ build/ *.egg-info/

# Build the package
echo -e "${YELLOW}Building the package...${NC}"
uv run python -m build

echo -e "${GREEN}Build completed successfully!${NC}"
echo "Package files are available in the 'dist' directory."
echo ""
echo -e "${YELLOW}To upload to PyPI (if you have access):${NC}"
echo "uv run python -m twine upload dist/*"
echo ""
echo -e "${YELLOW}To install locally:${NC}"
echo "uv pip install dist/*.whl"