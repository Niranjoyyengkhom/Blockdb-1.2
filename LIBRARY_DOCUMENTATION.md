# IEDB Library Documentation

IEDB (Integrated Encrypted Database) is a Python library that provides a lightweight blockchain-based database with integrated encryption, authentication, and REST API capabilities.

## Table of Contents

1. [Installation](#installation)
2. [Core Components](#core-components)
3. [Quick Start Guide](#quick-start-guide)
4. [Authentication](#authentication)
5. [Encryption](#encryption)
6. [API Integration](#api-integration)
7. [Advanced Features](#advanced-features)
8. [Configuration Options](#configuration-options)
9. [Best Practices](#best-practices)
10. [Contributing](#contributing)
11. [License](#license)

## Installation

### Using UV (recommended)

```bash
uv install iedb
```

### Using pip

```bash
pip install iedb
```

### From Source

```bash
git clone https://github.com/yourusername/iedb.git
cd iedb
uv install -e .
# or
pip install -e .
```

## Core Components

The IEDB library consists of four main modules:

### 1. Core Module

The core module provides the base database functionality with blockchain verification.

```python
from iedb.core import Database, BlockchainDB

# Create a simple database
db = Database('./mydata')

# Or use the blockchain-secured version
bdb = BlockchainDB('./blockchain_data')
```

### 2. API Module

The API module provides FastAPI integration for exposing your database via REST API.

```python
from iedb.api import APIManager

# Create API with default settings
api = APIManager(database=db)

# Run the API server
api.run(host="0.0.0.0", port=8000)
```

### 3. Security Module

The security module provides JWT-based authentication and user management.

```python
from iedb.security import JWTAuth

# Create auth manager
auth = JWTAuth(secret_key="your-secret-key")

# Create a token
token = auth.create_token({"user_id": "123"})

# Verify a token
payload = auth.verify_token(token)
```

### 4. Encryption Module

The encryption module provides file and data encryption using Fernet.

```python
from iedb.encryption import EncryptionManager

# Create encryption manager
enc = EncryptionManager("path/to/key/storage")

# Encrypt data
encrypted = enc.encrypt_data("sensitive information")

# Decrypt data
decrypted = enc.decrypt_data(encrypted)
```

## Quick Start Guide

Here's how to quickly set up a blockchain database with API and authentication:

```python
import uvicorn
from iedb.core import BlockchainDB
from iedb.api import APIManager
from iedb.security import JWTAuth, SecurityManager

# Create database
db = BlockchainDB('./mydb')

# Create auth manager
auth = JWTAuth(secret_key="your-secret-key")
security = SecurityManager(auth, user_db_path="./users.json")

# Create and register a test user (for first run)
security.register_user("admin", "password123")

# Create API with security
api = APIManager(
    database=db,
    security=security,
    title="My Secured DB API",
    description="Blockchain DB with JWT Authentication"
)

# Run the API
if __name__ == "__main__":
    uvicorn.run(api.app, host="0.0.0.0", port=8000)
```

## Authentication

IEDB provides a flexible authentication system based on JWT tokens:

### User Registration

```python
from iedb.security import SecurityManager, JWTAuth

auth = JWTAuth(secret_key="your-secret-key")
security = SecurityManager(auth, user_db_path="./users.json")

# Register a new user
success = security.register_user("username", "password")
```

### Token Generation

```python
# Authenticate and get token
token = security.authenticate("username", "password")
```

### Securing API Endpoints

```python
from iedb.api import APIManager
from fastapi import Depends

api = APIManager(database=db, security=security)

# The API will automatically set up secured endpoints
# You can access the auth dependency to create custom secured endpoints
auth_dependency = security.get_auth_dependency()

@api.app.get("/custom-secure-endpoint")
async def custom_secure(user = Depends(auth_dependency)):
    return {"message": "This is secure", "user": user}
```

## Encryption

IEDB provides robust encryption for both data and files:

### Data Encryption

```python
from iedb.encryption import EncryptionManager

# Create with default key storage location
enc = EncryptionManager()

# Encrypt and decrypt data
encrypted = enc.encrypt_data("sensitive information")
original = enc.decrypt_data(encrypted)
```

### File Encryption

```python
# Encrypt a file
enc.encrypt_file("secret.txt", "secret.enc")

# Decrypt a file
enc.decrypt_file("secret.enc", "secret_decrypted.txt")
```

### Custom Key Management

```python
# Generate a new encryption key
enc.generate_key("custom_key_name")

# Use a specific key
enc.set_active_key("custom_key_name")
```

## API Integration

IEDB comes with built-in FastAPI integration:

### Basic Setup

```python
from iedb.api import APIManager

api = APIManager(
    database=db,
    title="My DB API",
    description="API for accessing my database"
)

# Run the API
import uvicorn
uvicorn.run(api.app, host="0.0.0.0", port=8000)
```

### Custom Endpoints

```python
@api.app.get("/custom")
async def custom_endpoint():
    return {"message": "This is a custom endpoint"}
```

### API with Swagger Documentation

The API automatically includes Swagger documentation at `/docs`.

## Advanced Features

### Blockchain Verification

```python
from iedb.core import BlockchainDB

db = BlockchainDB('./mydb')

# Insert data
db.insert("users", {"id": "1", "name": "Alice"})

# Verify blockchain integrity
is_valid = db.verify_chain()
if not is_valid:
    print("WARNING: Data integrity compromised!")
```

### Database Backup and Restore

```python
# Backup the database
db.backup("./backup_location")

# Restore from backup
db.restore("./backup_location")
```

### Advanced Query Options

```python
# Find all users named "Alice"
results = db.find("users", {"name": "Alice"})

# Complex query with multiple conditions
results = db.find("users", {
    "age": {"$gt": 18},
    "status": "active"
})
```

## Configuration Options

IEDB can be configured through environment variables or directly in code:

### Environment Variables

- `IEDB_SECRET_KEY`: Secret key for JWT token generation
- `IEDB_TOKEN_EXPIRY`: Token expiry time in seconds
- `IEDB_KEY_LOCATION`: Path to encryption key storage
- `IEDB_API_HOST`: Default host for API server
- `IEDB_API_PORT`: Default port for API server

### Code Configuration

```python
from iedb.core import Database, DatabaseConfig

config = DatabaseConfig(
    storage_path="./custom_storage",
    transaction_log=True,
    max_size_mb=100,
    auto_backup=True,
    backup_interval=3600  # 1 hour
)

db = Database(config=config)
```

## Best Practices

1. **Key Management**: Store encryption keys securely, preferably in a different location from your data.
2. **Regular Backups**: Implement scheduled backups of your database.
3. **Password Policies**: Enforce strong password policies using the security module.
4. **Token Expiry**: Set appropriate token expiry times based on your security requirements.
5. **API Rate Limiting**: Consider implementing rate limiting for API endpoints.

## Contributing

We welcome contributions to IEDB! Please see our contributing guidelines in CONTRIBUTING.md.

## License

IEDB is licensed under the GNU General Public License v3.0 (GPL-3.0). See the LICENSE file for details.

Copyright (c) 2023-2024 niranjoyy@gmail.com