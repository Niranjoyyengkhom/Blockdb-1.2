#!/bin/bash

# IEDB Release Master Script
#
# This script runs all the necessary steps to:
# 1. Upload to GitHub
# 2. Create a .deb package
# 3. Create Windows executables
# 4. Publish all packages

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}====================================================${NC}"
echo -e "${YELLOW}      IEDB RELEASE AND DISTRIBUTION SCRIPT          ${NC}"
echo -e "${YELLOW}====================================================${NC}"

# First, validate the package
echo -e "\n${BLUE}Step 1: Validating package...${NC}"
if [ -f "./validate_package.sh" ]; then
    chmod +x ./validate_package.sh
    ./validate_package.sh
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Package validation failed. Aborting release process.${NC}"
        echo -e "${YELLOW}Please fix the issues and try again.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: Package validation script not found. Skipping validation.${NC}"
fi

# Upload to GitHub
echo -e "\n${BLUE}Step 2: Uploading to GitHub...${NC}"
if [ -f "./github_upload.sh" ]; then
    chmod +x ./github_upload.sh
    ./github_upload.sh
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}GitHub upload failed. Continuing with package creation...${NC}"
    else
        echo -e "${GREEN}GitHub upload completed.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: GitHub upload script not found. Skipping GitHub upload.${NC}"
fi

# Create .deb package
echo -e "\n${BLUE}Step 3: Creating .deb package...${NC}"
if [ -f "./create_deb_package.sh" ]; then
    chmod +x ./create_deb_package.sh
    ./create_deb_package.sh
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}DEB package creation failed. Continuing...${NC}"
    else
        echo -e "${GREEN}.deb package creation completed.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: DEB package script not found. Skipping DEB creation.${NC}"
fi

# Create Windows EXE
echo -e "\n${BLUE}Step 4: Creating Windows EXE package...${NC}"
if [ -f "./create_windows_exe.sh" ]; then
    chmod +x ./create_windows_exe.sh
    ./create_windows_exe.sh
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Windows EXE creation failed. Continuing...${NC}"
    else
        echo -e "${GREEN}Windows EXE package creation completed.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Windows EXE script not found. Skipping EXE creation.${NC}"
fi

# Upload to PyPI (if available)
echo -e "\n${BLUE}Step 5: Publishing to PyPI...${NC}"
if [ -f "./upload_pypi.sh" ]; then
    echo -e "${YELLOW}Do you want to publish to PyPI? (y/N)${NC}"
    read publish_pypi
    
    if [[ "$publish_pypi" =~ ^[Yy]$ ]]; then
        chmod +x ./upload_pypi.sh
        ./upload_pypi.sh
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}PyPI upload failed.${NC}"
        else
            echo -e "${GREEN}PyPI upload completed.${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping PyPI upload.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: PyPI upload script not found. Skipping PyPI upload.${NC}"
fi

# Upload packages to GitHub Release
echo -e "\n${BLUE}Step 6: Uploading packages to GitHub Release...${NC}"

# Check if gh CLI is installed
if command -v gh &> /dev/null; then
    echo -e "${YELLOW}Do you want to upload packages to GitHub Release? (y/N)${NC}"
    read upload_to_release
    
    if [[ "$upload_to_release" =~ ^[Yy]$ ]]; then
        # Check if gh is authenticated
        if ! gh auth status &> /dev/null; then
            echo -e "${YELLOW}Please authenticate with GitHub:${NC}"
            gh auth login
        fi
        
        echo -e "${YELLOW}Enter the tag/release name to upload to (e.g., v1.0.0):${NC}"
        read tag_name
        
        # Upload .deb package if it exists
        deb_pkg=$(ls -1 *.deb 2>/dev/null | head -1)
        if [ -n "$deb_pkg" ]; then
            echo -e "${YELLOW}Uploading .deb package to GitHub Release...${NC}"
            gh release upload "$tag_name" "$deb_pkg" --clobber
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}DEB package uploaded successfully.${NC}"
            else
                echo -e "${RED}Failed to upload DEB package.${NC}"
            fi
        fi
        
        # Upload Windows ZIP if it exists
        if [ -f "iedb_windows.zip" ]; then
            echo -e "${YELLOW}Uploading Windows package to GitHub Release...${NC}"
            gh release upload "$tag_name" "iedb_windows.zip" --clobber
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Windows package uploaded successfully.${NC}"
            else
                echo -e "${RED}Failed to upload Windows package.${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}Skipping GitHub Release upload.${NC}"
    fi
else
    echo -e "${YELLOW}GitHub CLI (gh) not found. Please install it to upload packages to GitHub Releases.${NC}"
fi

# Summary
echo -e "\n${BLUE}====================================================${NC}"
echo -e "${GREEN}IEDB RELEASE PROCESS COMPLETED${NC}"
echo -e "${BLUE}====================================================${NC}"
echo -e "${YELLOW}Release artifacts:${NC}"

# List created packages
if ls *.deb &>/dev/null; then
    echo -e "${GREEN}DEB Package: $(ls -1 *.deb)${NC}"
fi

if [ -f "dist/IEDB_Manager.exe" ]; then
    echo -e "${GREEN}Windows EXE: dist/IEDB_Manager.exe${NC}"
fi

if [ -f "iedb_windows.zip" ]; then
    echo -e "${GREEN}Windows ZIP: iedb_windows.zip${NC}"
fi

if ls dist/*.whl &>/dev/null; then
    echo -e "${GREEN}Python Wheel: $(ls -1 dist/*.whl)${NC}"
fi

if ls dist/*.tar.gz &>/dev/null; then
    echo -e "${GREEN}Source Distribution: $(ls -1 dist/*.tar.gz)${NC}"
fi

echo -e "\n${YELLOW}Thank you for using the IEDB Release Script!${NC}"