# IEDB Installation Instructions

## Quick Installation

You have two options to install the IEDB .deb package:

### Option 1: Run the automated installer
```bash
cd /home/niranjoy/Desktop/IEDB_Release
./install_iedb.sh
```

### Option 2: Manual step-by-step installation

1. **Install the .deb package:**
```bash
cd /home/niranjoy/Desktop/IEDB_Release
sudo dpkg -i packages/iedb_2.0.0.deb
```

2. **Fix any dependencies:**
```bash
sudo apt-get update
sudo apt-get install -f -y
```

3. **Install Python dependencies:**
```bash
sudo apt-get install -y python3 python3-pip python3-venv
```

4. **Create virtual environment and install packages:**
```bash
sudo python3 -m venv /usr/local/lib/iedb/venv
sudo /usr/local/lib/iedb/venv/bin/pip install fastapi uvicorn pyjwt passlib bcrypt email-validator cryptography python-multipart pydantic
```

5. **Start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable iedb
sudo service iedb start
```

6. **Check if it's running:**
```bash
sudo service iedb status
```

## After Installation

- **Web Interface:** http://localhost:8080
- **API Documentation:** http://localhost:8080/docs
- **Health Check:** http://localhost:8080/health

## Service Commands

```bash
sudo service iedb start           # Start IEDB
sudo service iedb stop            # Stop IEDB
sudo service iedb restart         # Restart IEDB
sudo service iedb status          # Check status
sudo journalctl -u iedb -f        # View logs
```