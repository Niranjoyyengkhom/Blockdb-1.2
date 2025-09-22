#!/bin/bash

# IEDB Installation Script
echo "🚀 Installing IEDB v2.0.0..."
echo "=========================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    echo "[INFO] Running as root..."
else
    echo "[INFO] This script requires sudo privileges for system installation."
    echo "[INFO] You will be prompted for your password."
fi

# Navigate to IEDB Release directory
cd /home/niranjoy/Desktop/IEDB_Release

# Install the .deb package
echo "[STEP 1/4] Installing IEDB package..."
sudo dpkg -i packages/iedb_2.0.0.deb

# Fix any dependency issues
echo "[STEP 2/4] Fixing dependencies..."
sudo apt-get update
sudo apt-get install -f -y

# Install Python dependencies system-wide
echo "[STEP 3/4] Installing Python dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv

# Set proper permissions
echo "[STEP 4/4] Setting permissions..."
sudo chmod +x /usr/local/bin/iedb
sudo chmod +x /usr/local/lib/iedb/deploy.sh
sudo chown -R root:root /usr/local/lib/iedb/
sudo chmod -R 755 /usr/local/lib/iedb/
sudo chmod 700 /usr/local/lib/iedb/auth_data/
sudo chmod 700 /usr/local/lib/iedb/encryption/

# Create Python virtual environment for IEDB
echo "[INFO] Creating Python virtual environment..."
sudo python3 -m venv /usr/local/lib/iedb/venv
sudo /usr/local/lib/iedb/venv/bin/pip install --upgrade pip

# Install required Python packages
echo "[INFO] Installing Python packages..."
sudo /usr/local/lib/iedb/venv/bin/pip install \
    fastapi \
    uvicorn \
    pyjwt \
    passlib \
    bcrypt \
    email-validator \
    cryptography \
    python-multipart \
    pydantic

# Update the iedb service to use virtual environment
sudo tee /lib/systemd/system/iedb.service > /dev/null << 'EOF'
[Unit]
Description=IEDB - Intelligent Enterprise Database
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/usr/local/lib/iedb
Environment=PYTHONPATH=/usr/local/lib/iedb
ExecStart=/usr/local/lib/iedb/venv/bin/python /usr/local/lib/iedb/iedb_api.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "[INFO] Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable iedb

# Start the service
echo "[INFO] Starting IEDB service..."
sudo service iedb start

# Check service status
echo "[INFO] Checking service status..."
sleep 3
sudo service iedb status

echo ""
echo "✅ IEDB Installation Complete!"
echo "=========================================="
echo "🌐 Web Interface: http://localhost:8080"
echo "📚 API Documentation: http://localhost:8080/docs"
echo "🔍 Health Check: http://localhost:8080/health"
echo ""
echo "Service Management Commands:"
echo "  sudo service iedb start       # Start service"
echo "  sudo service iedb stop        # Stop service"
echo "  sudo service iedb restart     # Restart service"
echo "  sudo service iedb status      # Check status"
echo ""
echo "View Logs:"
echo "  sudo journalctl -u iedb -f    # Follow logs"
echo "  sudo journalctl -u iedb       # View all logs"
echo ""
echo "🎉 IEDB is now ready to use!"