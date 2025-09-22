#!/bin/bash

# IEDB Library PyPI Upload Script
#
# This script uploads the IEDB library package to PyPI for public distribution.
# You need to have a PyPI account and .pypirc configuration set up.

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IEDB Library PyPI Upload Script ===${NC}"

# Check if .pypirc exists
if [ ! -f ~/.pypirc ]; then
    echo -e "${RED}No .pypirc file found. Creating template...${NC}"
    cat > ~/.pypirc << 'EOL'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = your_pypi_token_here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = your_testpypi_token_here
EOL

    echo -e "${YELLOW}Please edit ~/.pypirc and add your PyPI token before continuing.${NC}"
    echo -e "${BLUE}Press Enter to continue after editing, or Ctrl+C to cancel...${NC}"
    read
fi

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo -e "${RED}No distribution package found. Please run build_uv.sh first.${NC}"
    exit 1
fi

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo -e "${YELLOW}Installing twine...${NC}"
    pip install twine
fi

# Confirm upload
echo -e "${YELLOW}Are you ready to upload to PyPI? This cannot be undone. [y/N]${NC}"
read confirmation
if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Upload canceled.${NC}"
    exit 0
fi

# Ask if they want to upload to TestPyPI first
echo -e "${YELLOW}Would you like to upload to TestPyPI first? [Y/n]${NC}"
read test_first
if [[ ! "$test_first" =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}Uploading to TestPyPI...${NC}"
    twine upload --repository testpypi dist/*
    
    echo -e "${GREEN}Upload to TestPyPI complete!${NC}"
    echo -e "${YELLOW}You can install from TestPyPI with:${NC}"
    echo -e "uv pip install --index-url https://test.pypi.org/simple/ iedb"
    
    echo -e "${YELLOW}Do you want to continue uploading to PyPI? [y/N]${NC}"
    read continue_upload
    if [[ ! "$continue_upload" =~ ^[Yy]$ ]]; then
        echo -e "${RED}PyPI upload canceled.${NC}"
        exit 0
    fi
fi

# Upload to PyPI
echo -e "${YELLOW}Uploading to PyPI...${NC}"
twine upload dist/*

echo -e "${GREEN}Upload to PyPI complete!${NC}"
echo -e "${YELLOW}Your package can be installed with:${NC}"
echo -e "uv install iedb"
echo -e "pip install iedb"