#!/bin/bash

# IEDB .deb Package Creation Script
#
# This script creates a Debian package (.deb) for the IEDB library

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IEDB .deb Package Creation Script ===${NC}"

# Check if required tools are installed
if ! command -v dpkg-deb &> /dev/null || ! command -v fakeroot &> /dev/null; then
    echo -e "${YELLOW}Installing required packaging tools...${NC}"
    sudo apt update
    sudo apt install -y build-essential debhelper devscripts fakeroot
fi

# Get version from pyproject.toml or ask user
if [ -f "pyproject.toml" ]; then
    version=$(grep -oP 'version\s*=\s*"\K[^"]+' pyproject.toml)
else
    echo -e "${YELLOW}Enter package version (e.g., 1.0.0):${NC}"
    read version
fi

# Create a temporary directory structure for the package
pkg_root="$(pwd)/deb_dist"
pkg_name="iedb"
pkg_fullname="${pkg_name}_${version}"
pkg_dir="${pkg_root}/${pkg_fullname}"

echo -e "${YELLOW}Creating package directory structure...${NC}"
rm -rf "${pkg_root}"
mkdir -p "${pkg_dir}/DEBIAN"
mkdir -p "${pkg_dir}/usr/lib/python3/dist-packages/iedb"
mkdir -p "${pkg_dir}/usr/bin"
mkdir -p "${pkg_dir}/usr/share/doc/${pkg_name}"

# Create control file
cat > "${pkg_dir}/DEBIAN/control" << EOF
Package: ${pkg_name}
Version: ${version}
Section: python
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-pip, python3-fastapi, python3-cryptography
Maintainer: niranjoyy@gmail.com
Description: Integrated Encrypted Database with Blockchain features
 IEDB is a lightweight blockchain-based database with integrated
 encryption, authentication, and REST API capabilities.
 .
 Features include:
  * Blockchain Database: Store data with blockchain-level integrity verification
  * Encryption: Built-in encryption for sensitive data and files
  * Authentication: JWT-based user authentication and authorization
  * REST API: FastAPI integration for quickly exposing your database
EOF

# Create postinst script
cat > "${pkg_dir}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Install Python dependencies
pip3 install fastapi uvicorn cryptography pydantic python-jose passlib

# Set file permissions
chmod 755 /usr/bin/iedb

echo "IEDB package has been installed successfully."
EOF

chmod 755 "${pkg_dir}/DEBIAN/postinst"

# Create postrm script
cat > "${pkg_dir}/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

if [ "$1" = "remove" ]; then
    echo "IEDB package has been removed."
fi
EOF

chmod 755 "${pkg_dir}/DEBIAN/postrm"

# Copy Python package files
echo -e "${YELLOW}Copying package files...${NC}"
if [ -d "src/iedb" ]; then
    cp -r src/iedb/* "${pkg_dir}/usr/lib/python3/dist-packages/iedb/"
else
    echo -e "${RED}Source directory 'src/iedb' not found!${NC}"
    exit 1
fi

# Create executable script
cat > "${pkg_dir}/usr/bin/iedb" << 'EOF'
#!/usr/bin/env python3

import sys
import argparse
try:
    import iedb
except ImportError:
    print("Error: IEDB library not found. Please reinstall the package.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='IEDB Command Line Interface')
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--create-db', help='Create a new database at the specified path')
    parser.add_argument('--start-api', help='Start API server with database at specified path')
    parser.add_argument('--port', type=int, default=8000, help='Port for API server (default: 8000)')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"IEDB version {iedb.__version__}")
        return
    
    if args.create_db:
        from iedb.core import BlockchainDB
        db = BlockchainDB(args.create_db)
        print(f"Created new database at {args.create_db}")
        
    if args.start_api:
        from iedb.core import BlockchainDB
        from iedb.api import APIManager
        import uvicorn
        
        db = BlockchainDB(args.start_api)
        api = APIManager(
            database=db,
            title="IEDB API",
            description="Blockchain database API"
        )
        
        print(f"Starting API server with database at {args.start_api}")
        print(f"API documentation available at http://localhost:{args.port}/docs")
        uvicorn.run(api.app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
EOF

chmod 755 "${pkg_dir}/usr/bin/iedb"

# Copy documentation
cp LIBRARY_DOCUMENTATION.md "${pkg_dir}/usr/share/doc/${pkg_name}/README.md"
if [ -f "LICENSE" ]; then
    cp LICENSE "${pkg_dir}/usr/share/doc/${pkg_name}/copyright"
fi

# Build the package
echo -e "${YELLOW}Building .deb package...${NC}"
fakeroot dpkg-deb --build "${pkg_dir}"

# Move the package to the current directory
mv "${pkg_root}/${pkg_fullname}.deb" .

# Clean up
rm -rf "${pkg_root}"

if [ -f "${pkg_fullname}.deb" ]; then
    echo -e "${GREEN}Successfully created ${pkg_fullname}.deb${NC}"
    echo -e "${BLUE}Package information:${NC}"
    dpkg-deb -I "${pkg_fullname}.deb"
else
    echo -e "${RED}Failed to create .deb package${NC}"
    exit 1
fi

echo -e "${YELLOW}You can install the package with:${NC}"
echo -e "sudo dpkg -i ${pkg_fullname}.deb"
echo -e "sudo apt-get install -f  # To resolve any dependencies"