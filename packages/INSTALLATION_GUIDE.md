# IEDB Installation Guide

## Overview
IEDB (Intelligent Enterprise Database) v2.0.0 provides two installation packages:
- **iedb_2.0.0.deb** - Debian/Ubuntu Linux package
- **IEDB.exe** - Windows standalone executable

---

## 🐧 Linux Installation (.deb package)

### Prerequisites
- Ubuntu 18.04+ / Debian 10+ or compatible Linux distribution
- Python 3.9 or higher
- Root/sudo privileges for system installation

### Installation Steps

1. **Download the package**
   ```bash
   # Download iedb_2.0.0.deb to your system
   ```

2. **Install the package**
   ```bash
   sudo dpkg -i iedb_2.0.0.deb
   sudo apt-get install -f  # Fix any dependency issues
   ```

3. **Start IEDB service**
   ```bash
   sudo service iedb start
   sudo systemctl enable iedb  # Enable auto-start on boot
   ```

4. **Check service status**
   ```bash
   sudo service iedb status
   ```

5. **Access IEDB**
   - Web Interface: http://localhost:8080
   - API Documentation: http://localhost:8080/docs
   - Health Check: http://localhost:8080/health

### Service Management
```bash
sudo service iedb start         # Start service
sudo service iedb stop          # Stop service
sudo service iedb restart       # Restart service
sudo service iedb status        # Check status
```

### Logs
```bash
sudo journalctl -u iedb -f   # Follow service logs
sudo journalctl -u iedb      # View all service logs
```

### Uninstallation
```bash
sudo service iedb stop
sudo systemctl disable iedb
sudo dpkg -r iedb
```

---

## 🪟 Windows Installation (.exe)

### Prerequisites
- Windows 10 or higher
- No additional dependencies required (standalone executable)

### Installation Steps

1. **Download IEDB.exe**
   - Download IEDB.exe to your desired location
   - No installation required - it's a portable executable

2. **Run IEDB**
   ```cmd
   # Double-click IEDB.exe or run from command prompt:
   IEDB.exe
   ```

3. **Access IEDB**
   - Web Interface: http://localhost:8080
   - API Documentation: http://localhost:8080/docs
   - Health Check: http://localhost:8080/health

### Running as Windows Service (Optional)

1. **Install NSSM (Non-Sucking Service Manager)**
   - Download from: https://nssm.cc/download
   - Extract to a folder in your PATH

2. **Create Windows Service**
   ```cmd
   # Run as Administrator
   nssm install IEDB "C:\path\to\IEDB.exe"
   nssm set IEDB Description "IEDB - Intelligent Enterprise Database"
   nssm start IEDB
   ```

3. **Manage Service**
   ```cmd
   nssm start IEDB     # Start service
   nssm stop IEDB      # Stop service
   nssm restart IEDB   # Restart service
   nssm remove IEDB    # Remove service
   ```

---

## 🌐 First Time Setup

### 1. User Registration
```bash
curl -X POST "http://localhost:8080/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_secure_password",
    "email": "admin@yourcompany.com"
  }'
```

### 2. User Login
```bash
curl -X POST "http://localhost:8080/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_secure_password"
  }'
```

### 3. Create Your First Database
```bash
# Use the token from login response
TOKEN="your_jwt_token_here"

curl -X POST "http://localhost:8080/tenants/my_company/databases" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "main_db",
    "schema": "default"
  }'
```

---

## 🔧 Configuration

### Linux Configuration Files
- **Main Config**: `/etc/iedb/config.json`
- **Service File**: `/lib/systemd/system/iedb.service`
- **Application**: `/usr/local/lib/iedb/`
- **Logs**: `/var/log/iedb/`

### Windows Configuration
- Configuration files are stored in the same directory as IEDB.exe
- Data files are created in subdirectories relative to the executable

---

## 🚀 API Usage Examples

### Health Check
```bash
curl http://localhost:8080/health
```

### List Tenants
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/tenants
```

### Create Table
```bash
curl -X POST "http://localhost:8080/tenants/my_tenant/databases/my_db/tables" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "users",
    "schema": {"id": "INTEGER", "name": "TEXT", "email": "TEXT"},
    "table_name": "users",
    "columns": []
  }'
```

### Insert Data
```bash
curl -X POST "http://localhost:8080/tenants/my_tenant/databases/my_db/tables/users/data" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    }
  }'
```

---

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **ABAC Policies**: Attribute-Based Access Control
- **Data Encryption**: AES encryption for sensitive data
- **Multi-tenant**: Complete tenant isolation
- **Secure APIs**: All endpoints require authentication

---

## 📞 Support

### Documentation
- API Documentation: http://localhost:8080/docs
- Interactive API: http://localhost:8080/redoc

### Troubleshooting

**Linux Issues:**
```bash
# Check service status
sudo service iedb status

# View logs
sudo journalctl -u iedb -f

# Check port availability
sudo netstat -tulpn | grep 8080
```

**Windows Issues:**
- Check Windows Event Viewer for application errors
- Ensure Windows Firewall allows connections on port 8080
- Run IEDB.exe as Administrator if needed

### Default Ports
- **HTTP Server**: 8080
- **API Endpoints**: 8080/api/v1/*
- **Web Interface**: 8080/

---

## 📋 System Requirements

### Linux (.deb)
- **OS**: Ubuntu 18.04+ / Debian 10+
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Storage**: 100MB disk space minimum
- **Python**: 3.9 or higher

### Windows (.exe)
- **OS**: Windows 10 or higher
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Storage**: 100MB disk space minimum
- **Dependencies**: None (standalone executable)

---

## 🎯 Production Deployment

### Linux Production Setup
1. Install behind reverse proxy (nginx/apache)
2. Configure SSL/TLS certificates
3. Set up log rotation
4. Configure firewall rules
5. Enable service monitoring

### Windows Production Setup
1. Install as Windows Service using NSSM
2. Configure Windows Firewall
3. Set up SSL certificates if needed
4. Configure automatic startup
5. Set up monitoring and alerts

---

## 📄 License

IEDB v2.0.0 - Intelligent Enterprise Database
Released under GNU General Public License v3.0 (GPLv3)

For more information, visit: https://github.com/iedb/iedb
