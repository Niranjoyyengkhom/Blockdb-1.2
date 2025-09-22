# IEDB UV Package

This is a UV-compatible Python package for the IEDB (Intelligent Enterprise Database) project.

## Installation

### With UV (Recommended)

```bash
uv install iedb
```

### With pip

```bash
pip install iedb
```

## Usage

### Command Line Interface

The package provides a command-line interface for common operations:

```bash
# Start the IEDB server
iedb-cli server --host 0.0.0.0 --port 8000

# Initialize a new database
iedb-cli init --path ./my_database

# Create a backup
iedb-cli backup --source ./my_database --target ./backups

# Check version
iedb-cli version
```

### Python API

```python
from iedb import BlockchainDB

# Create a new database instance
db = BlockchainDB(storage_path="./my_database")

# Add data
db.insert("users", {"id": "user123", "name": "John Doe", "email": "john@example.com"})

# Query data
results = db.query("users", {"name": "John Doe"})

# Update data
db.update("users", "user123", {"email": "john.doe@example.com"})

# Delete data
db.delete("users", "user123")
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/Niranjoyyengkhom/Blockdb-1.2.git
cd Blockdb-1.2

# Install in development mode
uv pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3) - see the [LICENSE](LICENSE) file for details.

## Contact

- Email: niranjoyy@gmail.com
- GitHub: https://github.com/Niranjoyyengkhom/Blockdb-1.2