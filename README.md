# 🏢 IEDB v2.0.0 - Intelligent Enterprise Database

**Advanced file-based database system with encryption, AI features, JWT authentication, and blockchain-inspired storage**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![API Tests](https://img.shields.io/badge/API%20Tests-100%25%20Pass-brightgreen.svg)](/)

## 🚀 Features

### 🔐 **Security & Authentication**
- **JWT Authentication** - Secure token-based authentication system
- **ABAC (Attribute-Based Access Control)** - Fine-grained access control with dynamic policies
- **Encryption** - All data encrypted at rest using industry-standard algorithms
- **Multi-tenant Architecture** - Secure tenant isolation and management

### 📊 **Database Capabilities**
- **File-based Storage** - High-performance B-Tree indexing with encrypted storage
- **SQL & NoSQL Support** - Flexible query interface supporting both paradigms
- **ACID Compliance** - Transactional integrity with rollback capabilities
- **Schema Management** - Dynamic schema creation and validation
- **Advanced Querying** - Complex joins, aggregations, and filtering

### 🤖 **AI-Powered Features**
- **AI Query Generation** - Natural language to SQL conversion
- **Analytics Engine** - Automated data analysis and insights
- **Pattern Recognition** - Intelligent data trend identification
- **Predictive Analytics** - Future trend analysis and forecasting

### 🌐 **API & Integration**
- **RESTful API** - Complete REST API with 32 tested endpoints
- **OpenAPI/Swagger Documentation** - Interactive API documentation
- **FastAPI Framework** - High-performance async API framework
- **CORS Support** - Cross-origin resource sharing enabled

## 📦 Installation

### Quick Start (Recommended)

```bash
# Download and install IEDB
curl -O https://github.com/Niranjoyyengkhom/Blockdb-1.2/releases/latest/download/iedb_2.0.0.deb
sudo dpkg -i iedb_2.0.0.deb

# Start IEDB service
sudo systemctl start iedb
sudo systemctl enable iedb
```

### From Source

```bash
# Clone the repository
git clone https://github.com/Niranjoyyengkhom/Blockdb-1.2.git
cd Blockdb-1.2

# Install dependencies (requires Python 3.8+)
pip install uv
uv sync

# Start the server
./deploy.sh start
```

### Windows Installation

1. Download `IEDB.exe` from releases
2. Run the executable - no installation required!
3. Access via `http://localhost:4067`

## 🎯 Quick Usage

### Start IEDB Server
```bash
./deploy.sh start
```

### Access Points
- **Dashboard**: http://localhost:4067/
- **API Documentation**: http://localhost:4067/docs
- **Health Check**: http://localhost:4067/health

### Basic API Usage

```bash
# Register a user
curl -X POST http://localhost:4067/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secure123", "email": "admin@company.com"}'

# Login and get token
curl -X POST http://localhost:4067/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secure123"}'

# Create a database (use token from login)
curl -X POST http://localhost:4067/tenants/my_company/databases \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database_name": "products", "metadata": {"description": "Product catalog"}}'
```

## 📋 Management Commands

```bash
# Server Management
./deploy.sh start      # Start IEDB server
./deploy.sh stop       # Stop IEDB server
./deploy.sh restart    # Restart IEDB server
./deploy.sh status     # Show server status
./deploy.sh logs       # View server logs

# Package Building
./deploy.sh build      # Build standalone executable
./deploy.sh deb        # Create Debian (.deb) package
./deploy.sh exe        # Create Windows (.exe) package
./deploy.sh package    # Build all packages
```

## 🔧 Configuration

### Environment Variables
```bash
export IEDB_PORT=4067                    # Server port (default: 4067)
export JWT_SECRET_KEY=your_secret_key    # JWT signing key
export IEDB_LOG_LEVEL=info              # Logging level
```

### Directory Structure
```
IEDB/
├── src/                 # Source code
├── auth_data/           # User authentication data
├── encryption/          # Encryption keys and configs
├── tenants/            # Multi-tenant data storage
├── logs/               # Application logs
└── backups/            # Database backups
```

## 📊 API Endpoints Overview

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/profile` - User profile
- `POST /auth/logout` - User logout

### Database Operations
- `GET /tenants` - List all tenants
- `POST /tenants/{tenant_id}/databases` - Create database
- `GET /tenants/{tenant_id}/databases` - List databases
- `POST /tenants/{tenant_id}/databases/{db_name}/tables` - Create table
- `GET /tenants/{tenant_id}/databases/{db_name}/tables` - List tables

### Data Operations
- `POST /tenants/{tenant_id}/databases/{db_name}/tables/{table_name}/data` - Insert data
- `GET /tenants/{tenant_id}/databases/{db_name}/tables/{table_name}/data` - Query data
- `POST /tenants/{tenant_id}/databases/{db_name}/sql` - Execute SQL

### AI & Analytics
- `GET /api/v1/ai/capabilities` - AI capabilities
- `GET /api/v1/ai/analytics` - AI analytics
- `POST /api/v1/ai/generate-query` - Natural language to SQL

### Security
- `GET /abac/policies` - List ABAC policies
- `POST /abac/check-access` - Check access permissions
- `GET /abac/user-permissions` - User permissions

## 🧪 Testing

IEDB includes comprehensive testing with **100% API coverage**:

```bash
# Run comprehensive API tests
./test_100_percent.sh

# Expected output: 32/32 tests passing (100%)
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   JWT Auth      │    │   ABAC Engine   │
│   REST Server   │────│   Engine        │────│   Security      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Analytics  │    │   File Storage  │    │   Multi-tenant  │
│   Engine        │────│   B-Tree Index  │────│   Management    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Encryption    │    │   Backup &      │    │   Monitoring &  │
│   Layer         │────│   Recovery      │────│   Logging       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: Full API docs at `/docs` endpoint
- **Issues**: [GitHub Issues](https://github.com/Niranjoyyengkhom/Blockdb-1.2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Niranjoyyengkhom/Blockdb-1.2/discussions)

## 🎉 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for high-performance API
- Uses [UV](https://github.com/astral-sh/uv) for Python package management
- Inspired by modern database architectures and blockchain principles

---

**IEDB v2.0.0** - Making enterprise data management intelligent, secure, and scalable! 🚀