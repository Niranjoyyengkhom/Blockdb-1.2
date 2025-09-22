#!/bin/bash

# IEDB Library GitHub Packages Upload Script
#
# This script uploads the IEDB library package to GitHub Packages for distribution.
# You need to have a GitHub personal access token with package permissions.

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IEDB Library GitHub Packages Upload Script ===${NC}"

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}GitHub token not found in environment.${NC}"
    echo -e "${YELLOW}Please set your GitHub token:${NC}"
    echo -e "export GITHUB_TOKEN=your_github_token_here"
    exit 1
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

# Get GitHub username
echo -e "${YELLOW}Please enter your GitHub username:${NC}"
read github_username

# Get repository name
echo -e "${YELLOW}Please enter your repository name:${NC}"
read repo_name

# Confirm upload
echo -e "${YELLOW}Ready to upload to GitHub Packages (${github_username}/${repo_name})? [y/N]${NC}"
read confirmation
if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Upload canceled.${NC}"
    exit 0
fi

# Create or update .pypirc for GitHub Packages
cat > ~/.pypirc << EOL
[distutils]
index-servers =
    github

[github]
repository = https://upload.pypi.org/legacy/
username = ${github_username}
password = ${GITHUB_TOKEN}
EOL

# Upload to GitHub Packages
echo -e "${YELLOW}Uploading to GitHub Packages...${NC}"
twine upload --repository github dist/*

echo -e "${GREEN}Upload to GitHub Packages complete!${NC}"
echo -e "${YELLOW}Your package can be installed with:${NC}"
echo -e "uv pip install --index-url https://github.com/${github_username}/${repo_name}/releases/latest/download/ iedb"
echo -e "pip install --index-url https://github.com/${github_username}/${repo_name}/releases/latest/download/ iedb"