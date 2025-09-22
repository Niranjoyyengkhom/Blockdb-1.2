# IEDB - Intelligent Enterprise Database

A modern Python library for secure, blockchain-inspired database management with JWT authentication.

## Installation

### Using UV (Recommended)

```bash
uv install iedb
```

### Using pip

```bash
pip install iedb
```

## Quick Start

```python
from iedb.core import BlockchainDB
from iedb.encryption import EncryptionManager

# Initialize encryption
encryption = EncryptionManager()
encryption.save_key("my_encryption.key")

# Create a blockchain database
db = BlockchainDB("./data", "my_secure_db")

# Insert data into a collection
db.create_collection("users")
db.insert("users", {
    "name": "John Doe",
    "email": "john@example.com",
    "role": "admin"
})

# Query data
users = db.find("users", {"role": "admin"})
print(f"Found {len(users)} admin users")

# Add a block to the blockchain
db.add_block({
    "action": "user_created",
    "timestamp": "2025-09-22T15:30:00Z",
    "user_id": "123456"
})

# Verify blockchain integrity
is_valid = db.verify_blockchain()
print(f"Blockchain validity: {is_valid}")
```

## Create a REST API

```python
from iedb.core import BlockchainDB
from iedb.api import create_app
from iedb.security import SecurityManager

# Create database
db = BlockchainDB("./data", "api_db")

# Create security manager
security = SecurityManager()
jwt_auth = security.setup_jwt_auth(users_file="./users.json")

# Add a test user
jwt_auth.add_user(
    username="admin", 
    password="secure_password",
    email="admin@example.com"
)

# Create FastAPI application
app = create_app(
    db_instance=db,
    enable_security=True,
    auth_handler=jwt_auth
)

# Run with uvicorn
# uvicorn main:app --reload
```

## Features

- **File-based storage** with B-Tree indexing
- **Blockchain-inspired** data integrity
- **JWT Authentication** for secure API access
- **Strong encryption** using Fernet symmetric encryption
- **FastAPI integration** for high-performance REST APIs

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3) - see the [LICENSE](LICENSE) file for details.