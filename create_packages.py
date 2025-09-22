#!/usr/bin/env python3
"""
IEDB Package Creator
Creates .deb and .exe packages for IEDB distribution
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(f"Success: {result.stdout}")
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def create_exe_package():
    """Create Windows .exe package using PyInstaller"""
    print("\n🔧 Creating Windows .exe package...")
    
    # Create PyInstaller spec file
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['iedb_api.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('auth_data', 'auth_data'),
        ('encryption', 'encryption'),
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'uvicorn.main',
        'uvicorn.server',
        'fastapi',
        'pydantic',
        'jose',
        'passlib',
        'cryptography',
        'email_validator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='IEDB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='iedb_icon.ico' if os.path.exists('iedb_icon.ico') else None,
)
'''
    
    with open('IEDB.spec', 'w') as f:
        f.write(spec_content)
    
    # Create the executable
    success = run_command("uv run pyinstaller IEDB.spec --clean --onefile")
    
    if success and os.path.exists('dist/IEDB.exe'):
        print("✅ Windows .exe package created: dist/IEDB.exe")
        return True
    else:
        print("❌ Failed to create Windows .exe package")
        return False

def create_deb_package():
    """Create Debian .deb package"""
    print("\n📦 Creating Debian .deb package...")
    
    # Create package structure
    pkg_name = "iedb"
    pkg_version = "2.0.0"
    pkg_dir = f"{pkg_name}_{pkg_version}"
    
    if os.path.exists(pkg_dir):
        shutil.rmtree(pkg_dir)
    
    # Create directory structure
    dirs = [
        f"{pkg_dir}/DEBIAN",
        f"{pkg_dir}/usr/local/bin",
        f"{pkg_dir}/usr/local/lib/iedb",
        f"{pkg_dir}/etc/iedb",
        f"{pkg_dir}/var/log/iedb",
        f"{pkg_dir}/lib/systemd/system",
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # Create control file
    control_content = f'''Package: {pkg_name}
Version: {pkg_version}
Section: database
Priority: optional
Architecture: all
Depends: python3 (>= 3.9), python3-pip
Maintainer: IEDB Team <admin@iedb.com>
Description: IEDB - Intelligent Enterprise Database
 IEDB is a modern multi-tenant database system with JWT authentication,
 ABAC policies, and RESTful API interface.
 .
 This package provides the complete IEDB server with web interface.
'''
    
    with open(f"{pkg_dir}/DEBIAN/control", 'w') as f:
        f.write(control_content)
    
    # Create postinst script
    postinst_content = '''#!/bin/bash
set -e

# Create iedb user if it doesn't exist
if ! id "iedb" &>/dev/null; then
    useradd --system --home /var/lib/iedb --shell /bin/false iedb
fi

# Set permissions
chown -R iedb:iedb /var/log/iedb
chown -R iedb:iedb /etc/iedb
chown -R iedb:iedb /usr/local/lib/iedb

# Install Python dependencies
pip3 install fastapi uvicorn pydantic pyjwt passlib[bcrypt] python-multipart email-validator cryptography python-jose[cryptography]

# Enable and start service
systemctl daemon-reload
systemctl enable iedb
service iedb start

echo "IEDB installed successfully!"
echo "Access the web interface at: http://localhost:8080"
echo "API documentation at: http://localhost:8080/docs"
'''
    
    with open(f"{pkg_dir}/DEBIAN/postinst", 'w') as f:
        f.write(postinst_content)
    os.chmod(f"{pkg_dir}/DEBIAN/postinst", 0o755)
    
    # Create prerm script
    prerm_content = '''#!/bin/bash
set -e

# Stop and disable service
service iedb stop || true
systemctl disable iedb || true
'''
    
    with open(f"{pkg_dir}/DEBIAN/prerm", 'w') as f:
        f.write(prerm_content)
    os.chmod(f"{pkg_dir}/DEBIAN/prerm", 0o755)
    
    # Copy application files
    shutil.copy2('iedb_api.py', f"{pkg_dir}/usr/local/lib/iedb/")
    shutil.copy2('deploy.sh', f"{pkg_dir}/usr/local/lib/iedb/")
    
    # Copy data directories
    for data_dir in ['auth_data', 'encryption', 'templates']:
        if os.path.exists(data_dir):
            shutil.copytree(data_dir, f"{pkg_dir}/usr/local/lib/iedb/{data_dir}")
    
    # Create systemd service file
    service_content = '''[Unit]
Description=IEDB - Intelligent Enterprise Database
After=network.target

[Service]
Type=simple
User=iedb
Group=iedb
WorkingDirectory=/usr/local/lib/iedb
ExecStart=/usr/bin/python3 iedb_api.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
    
    with open(f"{pkg_dir}/lib/systemd/system/iedb.service", 'w') as f:
        f.write(service_content)
    
    # Create executable wrapper
    wrapper_content = '''#!/bin/bash
cd /usr/local/lib/iedb
python3 iedb_api.py "$@"
'''
    
    with open(f"{pkg_dir}/usr/local/bin/iedb", 'w') as f:
        f.write(wrapper_content)
    os.chmod(f"{pkg_dir}/usr/local/bin/iedb", 0o755)
    
    # Build the package
    success = run_command(f"dpkg-deb --build {pkg_dir}")
    
    if success and os.path.exists(f"{pkg_dir}.deb"):
        print(f"✅ Debian .deb package created: {pkg_dir}.deb")
        return True
    else:
        print("❌ Failed to create Debian .deb package")
        return False

def main():
    """Main package creation function"""
    print("🏢 IEDB Package Creator v2.0.0")
    print("=" * 50)
    
    # Ensure we're in the right directory
    if not os.path.exists('iedb_api.py'):
        print("❌ Error: iedb_api.py not found. Please run from IEDB_Release directory.")
        sys.exit(1)
    
    # Create packages directory
    os.makedirs('packages', exist_ok=True)
    
    success_count = 0
    
    # Create .deb package
    if create_deb_package():
        success_count += 1
        # Move to packages directory
        deb_file = [f for f in os.listdir('.') if f.endswith('.deb')][0]
        shutil.move(deb_file, f"packages/{deb_file}")
    
    # Create .exe package
    if create_exe_package():
        success_count += 1
        # Move to packages directory
        if os.path.exists('dist/IEDB.exe'):
            shutil.move('dist/IEDB.exe', 'packages/IEDB.exe')
    
    # Cleanup
    for cleanup_item in ['build', 'dist', '*.spec', 'iedb_*']:
        if os.path.exists(cleanup_item):
            if os.path.isdir(cleanup_item):
                shutil.rmtree(cleanup_item)
            else:
                os.remove(cleanup_item)
    
    print(f"\n🎉 Package creation completed!")
    print(f"✅ Successfully created {success_count}/2 packages")
    
    if os.path.exists('packages'):
        print("\n📦 Created packages:")
        for pkg in os.listdir('packages'):
            size = os.path.getsize(f"packages/{pkg}") / (1024*1024)
            print(f"   • {pkg} ({size:.1f} MB)")
    
    print(f"\n📍 Packages location: {os.path.abspath('packages')}")

if __name__ == "__main__":
    main()
