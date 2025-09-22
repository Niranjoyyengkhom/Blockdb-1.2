#!/usr/bin/env python3
"""IEDB Command-line interface.

This script provides command-line functionality for the IEDB package.
"""

import argparse
import logging
import os
import sys
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("iedb-cli")

def main():
    """Main entry point for the IEDB command-line tool."""
    parser = argparse.ArgumentParser(
        description="IEDB - Intelligent Enterprise Database CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Server command
    server_parser = subparsers.add_parser("server", help="Start the IEDB server")
    server_parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind to"
    )
    server_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to"
    )
    server_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload on code changes"
    )
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize a new IEDB database")
    init_parser.add_argument(
        "--path", type=str, default="./iedb_data", help="Path to store database files"
    )
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup the IEDB database")
    backup_parser.add_argument(
        "--source", type=str, default="./iedb_data", help="Source database path"
    )
    backup_parser.add_argument(
        "--target", type=str, default="./iedb_backup", help="Backup target path"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show IEDB version")
    
    args = parser.parse_args()
    
    if args.command == "server":
        start_server(args.host, args.port, args.reload)
    elif args.command == "init":
        initialize_database(args.path)
    elif args.command == "backup":
        backup_database(args.source, args.target)
    elif args.command == "version":
        show_version()
    else:
        parser.print_help()
        sys.exit(1)

def start_server(host: str, port: int, reload: bool):
    """Start the IEDB server."""
    import uvicorn
    
    try:
        # Import dynamically to avoid import issues when not needed
        from src.API import app
        
        logger.info(f"Starting IEDB server at http://{host}:{port}")
        uvicorn.run(
            "src.API:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )
    except ImportError as e:
        logger.error(f"Failed to import API module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

def initialize_database(path: str):
    """Initialize a new IEDB database."""
    try:
        # Import dynamically to avoid import issues when not needed
        from src.Database import initialization
        
        os.makedirs(path, exist_ok=True)
        logger.info(f"Initializing database at {path}")
        initialization.initialize_database(path)
        logger.info("Database initialization complete")
    except ImportError as e:
        logger.error(f"Failed to import Database module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)

def backup_database(source: str, target: str):
    """Backup the IEDB database."""
    try:
        import shutil
        from datetime import datetime
        
        # Create backup directory
        os.makedirs(target, exist_ok=True)
        
        # Create timestamped backup folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(target, f"iedb_backup_{timestamp}")
        
        logger.info(f"Backing up database from {source} to {backup_dir}")
        shutil.copytree(source, backup_dir)
        logger.info("Backup complete")
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        sys.exit(1)

def show_version():
    """Show IEDB version information."""
    try:
        from src import __version__
        print(f"IEDB version {__version__}")
    except ImportError:
        print("IEDB version 2.0.0")

if __name__ == "__main__":
    main()