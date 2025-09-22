#!/bin/bash

# IEDB GitHub Upload Script
#
# This script commits changes and pushes to GitHub repository

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IEDB GitHub Upload Script ===${NC}"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git is not installed. Please install git and try again.${NC}"
    exit 1
fi

# Check if we're inside a git repository
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo -e "${YELLOW}Not inside a git repository. Initializing new repository...${NC}"
    git init
    
    # Ask for remote repository URL
    echo -e "${YELLOW}Enter your GitHub repository URL (e.g., https://github.com/username/repo.git):${NC}"
    read repo_url
    
    # Add remote repository
    git remote add origin $repo_url
    echo -e "${GREEN}Repository initialized and remote added.${NC}"
else
    echo -e "${GREEN}Already inside a git repository.${NC}"
    
    # Display remote information
    echo -e "${YELLOW}Current remote repositories:${NC}"
    git remote -v
fi

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}No changes to commit.${NC}"
else
    # Add all changes
    echo -e "${YELLOW}Adding all changes to git...${NC}"
    git add .
    
    # Ask for commit message
    echo -e "${YELLOW}Enter commit message:${NC}"
    read commit_message
    
    # Commit changes
    git commit -m "$commit_message"
    echo -e "${GREEN}Changes committed.${NC}"
fi

# Push to GitHub
echo -e "${YELLOW}Pushing to GitHub repository...${NC}"
echo -e "${BLUE}This may require your GitHub credentials.${NC}"

# Ask which branch to push to
echo -e "${YELLOW}Enter branch name to push to (e.g., main, master):${NC}"
read branch_name

# Push changes
git push -u origin $branch_name

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully pushed to GitHub.${NC}"
else
    echo -e "${RED}Failed to push to GitHub. Please check your credentials and try again.${NC}"
    exit 1
fi

# Create a new release
echo -e "${YELLOW}Would you like to create a new GitHub release? [y/N]${NC}"
read create_release

if [[ "$create_release" =~ ^[Yy]$ ]]; then
    # Install gh CLI if not present
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}GitHub CLI not found. Installing...${NC}"
        sudo apt update
        sudo apt install -y gh
    fi
    
    # Check if gh is authenticated
    if ! gh auth status &> /dev/null; then
        echo -e "${YELLOW}Please authenticate with GitHub:${NC}"
        gh auth login
    fi
    
    # Get tag version
    echo -e "${YELLOW}Enter release version (e.g., v1.0.0):${NC}"
    read tag_version
    
    # Get release title
    echo -e "${YELLOW}Enter release title:${NC}"
    read release_title
    
    # Get release notes or use commit message
    echo -e "${YELLOW}Enter release notes or press enter to use commit message:${NC}"
    read release_notes
    
    if [ -z "$release_notes" ]; then
        release_notes=$commit_message
    fi
    
    # Create release
    echo -e "${YELLOW}Creating GitHub release...${NC}"
    
    # Create an annotated tag first
    git tag -a $tag_version -m "$release_title"
    git push origin $tag_version
    
    # Create the release
    gh release create $tag_version -t "$release_title" -n "$release_notes"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}GitHub release created successfully.${NC}"
    else
        echo -e "${RED}Failed to create GitHub release.${NC}"
    fi
fi

echo -e "${GREEN}GitHub upload process completed.${NC}"