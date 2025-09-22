#!/bin/bash

# IEDB Library Package Validation Script
#
# This script validates the IEDB library package before publishing to ensure quality.

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IEDB Library Package Validation ===${NC}"

# Check if distribution exists
if [ ! -d "dist" ]; then
    echo -e "${RED}No distribution package found. Please run build_uv.sh first.${NC}"
    exit 1
fi

# Create a temporary virtual environment for testing
echo -e "${YELLOW}Creating temporary test environment...${NC}"
python -m venv .validate_env
source .validate_env/bin/activate

# Install the built package
echo -e "${YELLOW}Installing local package for validation...${NC}"
pip install --find-links=dist/ iedb

# Run validation tests
echo -e "${YELLOW}Running basic package validation tests...${NC}"

# Test package import
echo -e "${BLUE}Testing package import...${NC}"
IMPORT_TEST=$(python -c "
try:
    import iedb
    print(f'Successfully imported iedb version {iedb.__version__}')
    import iedb.core
    import iedb.api
    import iedb.security
    import iedb.encryption
    print('All modules imported successfully')
    exit(0)
except Exception as e:
    print(f'Error importing package: {e}')
    exit(1)
")

if [ $? -ne 0 ]; then
    echo -e "${RED}Package import test failed:${NC}"
    echo "$IMPORT_TEST"
    validation_failed=true
else
    echo -e "${GREEN}Package import test successful:${NC}"
    echo "$IMPORT_TEST"
fi

# Test basic functionality
echo -e "${BLUE}Testing basic functionality...${NC}"
FUNC_TEST=$(python -c "
try:
    from iedb.core import Database
    
    # Create a test database
    db = Database('./temp_test_db')
    
    # Test basic operations
    db.insert('test_collection', {'id': '1', 'name': 'test_item'})
    result = db.get('test_collection', '1')
    assert result and result['name'] == 'test_item', 'Data retrieval failed'
    
    db.update('test_collection', '1', {'name': 'updated_item'})
    result = db.get('test_collection', '1')
    assert result and result['name'] == 'updated_item', 'Data update failed'
    
    db.delete('test_collection', '1')
    result = db.get('test_collection', '1')
    assert not result, 'Data deletion failed'
    
    # Clean up
    import shutil
    shutil.rmtree('./temp_test_db', ignore_errors=True)
    
    print('Basic functionality test passed')
    exit(0)
except Exception as e:
    print(f'Error in functionality test: {e}')
    exit(1)
")

if [ $? -ne 0 ]; then
    echo -e "${RED}Functionality test failed:${NC}"
    echo "$FUNC_TEST"
    validation_failed=true
else
    echo -e "${GREEN}Functionality test successful:${NC}"
    echo "$FUNC_TEST"
fi

# Check wheel structure
echo -e "${BLUE}Validating wheel structure...${NC}"
if command -v check-wheel-contents &> /dev/null; then
    WHEEL_CHECK=$(check-wheel-contents dist/*.whl)
    if [ $? -ne 0 ]; then
        echo -e "${RED}Wheel structure check failed:${NC}"
        echo "$WHEEL_CHECK"
        validation_failed=true
    else
        echo -e "${GREEN}Wheel structure check passed${NC}"
    fi
else
    echo -e "${YELLOW}Installing wheel validation tools...${NC}"
    pip install wheel-inspect check-wheel-contents
    WHEEL_CHECK=$(check-wheel-contents dist/*.whl)
    if [ $? -ne 0 ]; then
        echo -e "${RED}Wheel structure check failed:${NC}"
        echo "$WHEEL_CHECK"
        validation_failed=true
    else
        echo -e "${GREEN}Wheel structure check passed${NC}"
    fi
fi

# Validate package metadata
echo -e "${BLUE}Validating package metadata...${NC}"
META_CHECK=$(python -m pip show iedb)
echo "$META_CHECK"

# Clean up
echo -e "${YELLOW}Cleaning up validation environment...${NC}"
deactivate
rm -rf .validate_env

# Final report
if [ "$validation_failed" = true ]; then
    echo -e "${RED}=== Package validation FAILED ===${NC}"
    echo -e "${YELLOW}Please fix the issues before publishing.${NC}"
    exit 1
else
    echo -e "${GREEN}=== Package validation PASSED ===${NC}"
    echo -e "${GREEN}The package is ready for publication!${NC}"
fi