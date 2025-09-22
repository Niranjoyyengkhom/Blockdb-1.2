#!/usr/bin/env bash

# Script to publish IEDB package to PyPI or TestPyPI
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default settings
USE_TESTPYPI=false
SKIP_BUILD=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --test)
      USE_TESTPYPI=true
      shift
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  --test       Publish to TestPyPI instead of PyPI"
      echo "  --skip-build Skip the build step (use existing dist files)"
      echo "  --help       Show this help message"
      exit 0
      ;;
    *)
      # Unknown option
      echo "Unknown option: $arg"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Check PyPI configuration
if [ ! -f ~/.pypirc ]; then
    echo -e "${RED}PyPI configuration file ~/.pypirc not found.${NC}"
    echo "Please create it with your PyPI credentials. A template is provided in pypirc_template."
    echo "Example:"
    echo "    cp pypirc_template ~/.pypirc"
    echo "    nano ~/.pypirc  # Replace <your-pypi-token> with your actual token"
    echo "    chmod 600 ~/.pypirc"
    exit 1
fi

# Build the package if not skipped
if [ "$SKIP_BUILD" = false ]; then
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
fi

# Set the repository flag based on the target
if [ "$USE_TESTPYPI" = true ]; then
    REPO_FLAG="--repository testpypi"
    echo -e "${YELLOW}Publishing to TestPyPI...${NC}"
else
    REPO_FLAG=""
    echo -e "${YELLOW}Publishing to PyPI...${NC}"
fi

# Upload to PyPI or TestPyPI
echo -e "${YELLOW}Uploading package to repository...${NC}"
uv run python -m twine upload $REPO_FLAG dist/*

# Print installation instructions
if [ "$USE_TESTPYPI" = true ]; then
    echo -e "${GREEN}Package published to TestPyPI!${NC}"
    echo "To install from TestPyPI:"
    echo "uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ iedb"
else
    echo -e "${GREEN}Package published to PyPI!${NC}"
    echo "To install from PyPI:"
    echo "uv pip install iedb"
fi