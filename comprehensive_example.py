#!/usr/bin/env python3
"""
IEDB Library Comprehensive Example

This script demonstrates the full capabilities of the IEDB library,
including database operations, blockchain verification, API integration,
authentication, and encryption.

To run this example:
1. Install the IEDB library: `uv install iedb` or `pip install iedb`
2. Run this script: `python comprehensive_example.py`
3. Visit http://localhost:8000/docs to interact with the API
"""

import os
import sys
import time
import asyncio
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
import json
import uuid
import threading
import webbrowser
from typing import Dict, List, Optional, Any

try:
    import iedb
    from iedb.core import Database, BlockchainDB
    from iedb.api import APIManager
    from iedb.security import JWTAuth, SecurityManager
    from iedb.encryption import EncryptionManager
except ImportError:
    print("Error: IEDB library not found. Please install it with:")
    print("  uv install iedb  # or")
    print("  pip install iedb")
    sys.exit(1)

# Configuration
DATA_DIR = "./example_data"
USER_DB = f"{DATA_DIR}/users.json"
ENCRYPTED_FILE = f"{DATA_DIR}/encrypted.dat"
DECRYPTED_FILE = f"{DATA_DIR}/decrypted.txt"
API_HOST = "127.0.0.1"
API_PORT = 8000

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

print(f"IEDB Library Example (version {iedb.__version__})")
print("=" * 50)

# Initialize components
print("Initializing components...")
db = BlockchainDB(f"{DATA_DIR}/blockchain_db")
enc = EncryptionManager(f"{DATA_DIR}/keys")
auth = JWTAuth(secret_key="example-secret-key-change-this-in-production")
security = SecurityManager(auth, user_db_path=USER_DB)

# Sample data for our database
sample_data = [
    {"id": str(uuid.uuid4()), "name": "Alice", "role": "admin", "age": 30},
    {"id": str(uuid.uuid4()), "name": "Bob", "role": "user", "age": 25},
    {"id": str(uuid.uuid4()), "name": "Charlie", "role": "user", "age": 35},
    {"id": str(uuid.uuid4()), "name": "Diana", "role": "manager", "age": 40},
    {"id": str(uuid.uuid4()), "name": "Eve", "role": "user", "age": 22}
]

# Setup the database with sample data
print("Setting up database with sample data...")
for item in sample_data:
    db.insert("users", item)
    print(f"  Added user: {item['name']}")

# Verify blockchain integrity
print("\nVerifying blockchain integrity...")
if db.verify_chain():
    print("  ✅ Blockchain integrity verified")
else:
    print("  ❌ Blockchain integrity check failed")

# Test basic database operations
print("\nPerforming database operations:")
user_id = sample_data[0]["id"]

# Get operation
print(f"  Get user by ID: {user_id}")
user = db.get("users", user_id)
print(f"  Retrieved: {user['name']} (role: {user['role']})")

# Update operation
print(f"  Updating user {user['name']}")
db.update("users", user_id, {"age": 31, "role": "superadmin"})
updated_user = db.get("users", user_id)
print(f"  Updated: {updated_user['name']} (role: {updated_user['role']}, age: {updated_user['age']})")

# Find operation
print("  Finding users with role 'user':")
users = db.find("users", {"role": "user"})
for user in users:
    print(f"    - {user['name']} (age: {user['age']})")

# Encryption example
print("\nTesting encryption functionality:")

# Data encryption
sensitive_data = "This is sensitive information that needs encryption"
print(f"  Original data: '{sensitive_data}'")
encrypted = enc.encrypt_data(sensitive_data)
print(f"  Encrypted: {encrypted[:20]}...")
decrypted = enc.decrypt_data(encrypted)
print(f"  Decrypted: '{decrypted}'")

# File encryption
print("  Creating sample file for encryption...")
with open(DECRYPTED_FILE, "w") as f:
    f.write("TOP SECRET: This file contains classified information.\n")
    f.write("Do not distribute without authorization.")

print(f"  Encrypting file: {DECRYPTED_FILE} -> {ENCRYPTED_FILE}")
enc.encrypt_file(DECRYPTED_FILE, ENCRYPTED_FILE)
print(f"  Decrypting file: {ENCRYPTED_FILE} -> {DECRYPTED_FILE}.restored")
enc.decrypt_file(ENCRYPTED_FILE, f"{DECRYPTED_FILE}.restored")

# Security and user management
print("\nSetting up user authentication:")

# Create users
print("  Creating sample users...")
security.register_user("admin", "admin123")
security.register_user("user", "password123")
print("  Users created")

# Authenticate
print("  Authenticating as admin...")
admin_token = security.authenticate("admin", "admin123")
if admin_token:
    print(f"  ✅ Authentication successful, token received")
    print(f"  Token: {admin_token[:20]}...")
else:
    print("  ❌ Authentication failed")

print("  Testing invalid credentials...")
invalid_token = security.authenticate("admin", "wrongpassword")
if not invalid_token:
    print("  ✅ Invalid authentication correctly rejected")
else:
    print("  ❌ Security issue: Invalid credentials accepted")

# Set up API with all components
print("\nSetting up API with all components...")
api = APIManager(
    database=db,
    security=security,
    encryption=enc,
    title="IEDB Complete Example",
    description="Demonstration of all IEDB library features",
    version=iedb.__version__
)

# Add some custom endpoints
@api.app.get("/stats", tags=["Custom"])
async def stats():
    """Get database statistics"""
    user_count = len(db.find("users", {}))
    collections = db.list_collections()
    return {
        "collections": collections,
        "user_count": user_count,
        "blockchain_valid": db.verify_chain()
    }

@api.app.get("/secured-stats", tags=["Custom"])
async def secured_stats(user = Depends(security.get_auth_dependency())):
    """Get detailed statistics (requires authentication)"""
    user_count = len(db.find("users", {}))
    collections = db.list_collections()
    all_users = db.find("users", {})
    
    # Calculate age distribution
    age_distribution = {}
    for user in all_users:
        age_group = f"{user['age'] // 10 * 10}s"  # Group by decades
        if age_group in age_distribution:
            age_distribution[age_group] += 1
        else:
            age_distribution[age_group] = 1
            
    return {
        "collections": collections,
        "user_count": user_count,
        "blockchain_valid": db.verify_chain(),
        "age_distribution": age_distribution,
        "authenticated_as": user
    }

# Launch the API server in a separate thread
def run_api_server():
    print(f"\nStarting API server at http://{API_HOST}:{API_PORT}")
    print(f"API documentation available at http://{API_HOST}:{API_PORT}/docs")
    uvicorn.run(api.app, host=API_HOST, port=API_PORT)

# Instructions for testing the API
def print_api_usage():
    print("\n" + "=" * 50)
    print("API TESTING INSTRUCTIONS")
    print("=" * 50)
    print("\nThe API server is now running with these endpoints:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("\nAuthentication credentials:")
    print("  - Username: admin")
    print("  - Password: admin123")
    print("\nTo test the API using curl:")
    print("\n1. Get a token:")
    print('   curl -X POST "http://localhost:8000/token" -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin&password=admin123"')
    print("\n2. Use the token to access secured endpoints:")
    print('   curl -X GET "http://localhost:8000/api/users" -H "Authorization: Bearer YOUR_TOKEN_HERE"')
    print("\n3. Access public stats:")
    print('   curl -X GET "http://localhost:8000/stats"')
    print("\n4. Access secured stats (requires token):")
    print('   curl -X GET "http://localhost:8000/secured-stats" -H "Authorization: Bearer YOUR_TOKEN_HERE"')
    print("\nPress Ctrl+C to stop the server and exit.")
    print("=" * 50)

# Open browser with the Swagger UI
def open_browser():
    time.sleep(2)  # Wait for server to start
    webbrowser.open(f"http://{API_HOST}:{API_PORT}/docs")

if __name__ == "__main__":
    # Start the API server in a separate thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Open browser to show the Swagger UI
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Print API usage instructions
    print_api_usage()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)