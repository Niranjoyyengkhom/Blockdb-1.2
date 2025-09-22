#!/bin/bash

# IEDB v2.0.0 - Production Deployment & Packaging Script
# =====================================================

set -e

IEDB_VERSION="2.0.0"
IEDB_PORT=${IEDB_PORT:-4067}
PID_FILE="iedb.pid"
LOG_FILE="logs/iedb.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_header() {
    echo -e "${PURPLE}🏢 IEDB v$IEDB_VERSION - $1${NC}"
    echo "==============================================="
}

print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_step() { echo -e "${YELLOW}[STEP]${NC} $1"; }

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

init_directories() {
    print_step "Initializing directories..."
    mkdir -p data auth_data encryption logs tenants backups
    chmod 700 auth_data encryption
    print_success "Directories created"
}

start_server() {
    print_header "STARTING IEDB SERVER"
    
    if is_running; then
        print_info "IEDB server is already running (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    init_directories
    
    print_step "Installing dependencies..."
    uv sync --quiet
    
    print_step "Starting IEDB server on port $IEDB_PORT..."
    uv run python src/API/iedb_api.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 3
    
    if is_running; then
        print_success "IEDB server started successfully!"
        print_info "Process ID: $(cat $PID_FILE)"
        print_info "Port: $IEDB_PORT"
        print_info "Dashboard: http://localhost:$IEDB_PORT/"
        print_info "API Docs: http://localhost:$IEDB_PORT/docs"
    else
        print_error "Failed to start server. Check logs: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop_server() {
    print_header "STOPPING IEDB SERVER"
    
    if ! is_running; then
        print_info "IEDB server is not running"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    print_step "Stopping IEDB server (PID: $pid)..."
    
    kill $pid 2>/dev/null || true
    sleep 2
    
    if is_running; then
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
    
    rm -f "$PID_FILE"
    print_success "IEDB server stopped"
}

server_status() {
    print_header "IEDB SERVER STATUS"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_success "IEDB server is running (PID: $pid)"
        print_info "Port: $IEDB_PORT"
        
        if command -v curl >/dev/null 2>&1; then
            if curl -s -f "http://localhost:$IEDB_PORT/health" >/dev/null; then
                print_success "✅ Health check: OK"
            else
                print_error "❌ Health check: Failed"
            fi
        fi
    else
        print_error "IEDB server is not running"
        return 1
    fi
}

build_executable() {
    print_header "BUILDING EXECUTABLE PACKAGES"
    
    print_step "Installing packaging tools..."
    uv add --group packaging pyinstaller
    
    mkdir -p build dist
    
    print_step "Building standalone executable..."
    uv run pyinstaller \
        --onefile \
        --name iedb \
        --distpath dist \
        --workpath build \
        --add-data "src:src" \
        --hidden-import uvicorn \
        --hidden-import fastapi \
        --hidden-import src.API.iedb_api \
        src/API/iedb_api.py
    
    if [ $? -eq 0 ]; then
        print_success "Executable built: dist/iedb"
        ls -lh dist/iedb
    else
        print_error "Failed to build executable"
        return 1
    fi
}

create_deb_package() {
    print_step "Creating Debian package..."
    
    local deb_dir="build/iedb-deb"
    rm -rf "$deb_dir"
    
    # Package structure
    mkdir -p "$deb_dir"/{DEBIAN,usr/bin,usr/share/iedb,etc/iedb,var/lib/iedb,var/log/iedb}
    
    # Copy files
    cp dist/iedb "$deb_dir/usr/bin/"
    cp -r src "$deb_dir/usr/share/iedb/"
    
    # Control file
    cat > "$deb_dir/DEBIAN/control" << EOF
Package: iedb
Version: $IEDB_VERSION
Section: database
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.9)
Maintainer: IEDB Team <team@iedb.com>
Description: Intelligent Enterprise Database
 Production-grade multi-tenant database with advanced security features.
 Features JWT authentication, ABAC authorization, and AES-256 encryption.
EOF
    
    # Post-install script
    cat > "$deb_dir/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e
if ! id iedb >/dev/null 2>&1; then
    useradd --system --home /var/lib/iedb --shell /bin/false iedb
fi
chown -R iedb:iedb /var/lib/iedb /var/log/iedb
chmod 755 /usr/bin/iedb

if [ -d /etc/systemd/system ]; then
    cat > /etc/systemd/system/iedb.service << 'SERVICE'
[Unit]
Description=IEDB - Intelligent Enterprise Database
After=network.target

[Service]
Type=simple
User=iedb
Group=iedb
WorkingDirectory=/var/lib/iedb
ExecStart=/usr/bin/iedb
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

    systemctl daemon-reload
    systemctl enable iedb
    echo "IEDB installed! Start with: sudo systemctl start iedb"
fi
EOF
    
    chmod 755 "$deb_dir/DEBIAN/postinst"
    
    # Build package
    local deb_file="dist/iedb_${IEDB_VERSION}_amd64.deb"
    dpkg-deb --build "$deb_dir" "$deb_file"
    
    if [ $? -eq 0 ]; then
        print_success "Debian package: $deb_file"
        ls -lh "$deb_file"
    else
        print_error "Failed to create Debian package"
        return 1
    fi
}

create_windows_package() {
    print_step "Creating Windows package..."
    
    # Build Windows executable
    uv run pyinstaller \
        --onefile \
        --name iedb.exe \
        --distpath dist \
        --workpath build/win \
        --add-data "src;src" \
        --hidden-import uvicorn \
        --hidden-import fastapi \
        --console \
        src/API/iedb_api.py
    
    if [ $? -eq 0 ]; then
        print_success "Windows executable: dist/iedb.exe"
        
        # Create installer
        cat > "dist/install_iedb.bat" << 'BAT'
@echo off
echo Installing IEDB v2.0.0 for Windows...

if not exist "C:\Program Files\IEDB" mkdir "C:\Program Files\IEDB"
if not exist "C:\ProgramData\IEDB" mkdir "C:\ProgramData\IEDB"
if not exist "C:\ProgramData\IEDB\logs" mkdir "C:\ProgramData\IEDB\logs"

copy iedb.exe "C:\Program Files\IEDB\"

echo @echo off > "C:\Program Files\IEDB\start_iedb.bat"
echo cd "C:\ProgramData\IEDB" >> "C:\Program Files\IEDB\start_iedb.bat"
echo "C:\Program Files\IEDB\iedb.exe" >> "C:\Program Files\IEDB\start_iedb.bat"

echo IEDB installed successfully!
echo Run: "C:\Program Files\IEDB\start_iedb.bat"
echo Open: http://localhost:8080
pause
BAT
        
        print_info "Windows installer: dist/install_iedb.bat"
        ls -lh dist/iedb.exe
    else
        print_error "Failed to create Windows package"
        return 1
    fi
}

case "${1:-help}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 2
        start_server
        ;;
    status)
        server_status
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            print_error "Log file not found: $LOG_FILE"
        fi
        ;;
    build)
        build_executable
        ;;
    deb)
        build_executable
        create_deb_package
        ;;
    exe)
        build_executable
        create_windows_package
        ;;
    package)
        build_executable
        create_deb_package
        create_windows_package
        print_success "All packages created in dist/ directory"
        ;;
    *)
        echo -e "${PURPLE}IEDB v$IEDB_VERSION - Deployment Script${NC}"
        echo "Usage: $0 [start|stop|restart|status|logs|build|deb|exe|package]"
        echo
        echo "Commands:"
        echo "  start    - Start IEDB server"
        echo "  stop     - Stop IEDB server"
        echo "  restart  - Restart IEDB server"
        echo "  status   - Show server status"
        echo "  logs     - View server logs"
        echo "  build    - Build standalone executable"
        echo "  deb      - Create Debian (.deb) package"
        echo "  exe      - Create Windows (.exe) package"
        echo "  package  - Build all packages"
        echo
        echo "Environment:"
        echo "  IEDB_PORT - Server port (default: 8080)"
        ;;
esac