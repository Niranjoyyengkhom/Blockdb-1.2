#!/bin/bash

# IEDB Windows EXE Package Creation Script
#
# This script creates Windows executables (.exe) for the IEDB library using PyInstaller

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IEDB Windows EXE Package Creation Script ===${NC}"

# Check if PyInstaller is installed
if ! python -c "import PyInstaller" &> /dev/null; then
    echo -e "${YELLOW}Installing PyInstaller...${NC}"
    pip install pyinstaller
fi

# Check if required Windows tools are installed for cross-compilation
if ! command -v wine &> /dev/null; then
    echo -e "${YELLOW}Wine is required for Windows builds. Installing...${NC}"
    sudo apt update
    sudo apt install -y wine wine64 wine32
fi

# Check if Python for Windows is available
if ! command -v python3-wine &> /dev/null; then
    echo -e "${YELLOW}Installing Python for Windows via Wine...${NC}"
    
    # Create a temporary directory
    mkdir -p temp_win_install
    cd temp_win_install
    
    # Download Python installer for Windows
    echo -e "${BLUE}Downloading Python for Windows...${NC}"
    wget https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe
    
    # Install Python silently using Wine
    echo -e "${BLUE}Installing Python for Windows using Wine...${NC}"
    wine python-3.9.7-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
    
    # Clean up
    cd ..
    rm -rf temp_win_install
fi

# Create a Windows executable wrapper script
cat > "iedb_win_wrapper.py" << 'EOF'
#!/usr/bin/env python3
"""
IEDB Windows Application Wrapper
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import tempfile
import webbrowser

# Set path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import iedb
    from iedb.core import Database, BlockchainDB
    from iedb.api import APIManager
    from iedb.security import JWTAuth, SecurityManager
    from iedb.encryption import EncryptionManager
except ImportError:
    messagebox.showerror("Import Error", "Failed to import IEDB library. Please ensure it's installed correctly.")
    sys.exit(1)

class IEDBApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"IEDB Manager v{iedb.__version__}")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        self.server_thread = None
        self.api = None
        self.db = None
        self.db_path = None
        self.api_running = False
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create tabs
        self.db_tab = ttk.Frame(self.notebook, padding="10")
        self.api_tab = ttk.Frame(self.notebook, padding="10")
        self.encryption_tab = ttk.Frame(self.notebook, padding="10")
        self.about_tab = ttk.Frame(self.notebook, padding="10")
        
        self.notebook.add(self.db_tab, text="Database")
        self.notebook.add(self.api_tab, text="API Server")
        self.notebook.add(self.encryption_tab, text="Encryption")
        self.notebook.add(self.about_tab, text="About")
        
        # Setup tabs
        self.setup_db_tab()
        self.setup_api_tab()
        self.setup_encryption_tab()
        self.setup_about_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_db_tab(self):
        # Database path section
        path_frame = ttk.LabelFrame(self.db_tab, text="Database Location", padding="10")
        path_frame.pack(fill=tk.X, pady=5)
        
        self.db_path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.db_path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_btn = ttk.Button(path_frame, text="Browse", command=self.browse_db_path)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        create_btn = ttk.Button(path_frame, text="Create/Open DB", command=self.create_db)
        create_btn.pack(side=tk.LEFT, padx=5)
        
        # Database operations section
        ops_frame = ttk.LabelFrame(self.db_tab, text="Database Operations", padding="10")
        ops_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Collection selection
        coll_frame = ttk.Frame(ops_frame)
        coll_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(coll_frame, text="Collection:").pack(side=tk.LEFT, padx=5)
        self.collection_var = tk.StringVar()
        self.collection_entry = ttk.Entry(coll_frame, textvariable=self.collection_var, width=20)
        self.collection_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        refresh_btn = ttk.Button(coll_frame, text="Refresh Collections", command=self.refresh_collections)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Collections list
        list_frame = ttk.Frame(ops_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.collections_listbox = tk.Listbox(list_frame, height=5)
        self.collections_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.collections_listbox.bind('<<ListboxSelect>>', self.on_collection_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.collections_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.collections_listbox.config(yscrollcommand=scrollbar.set)
        
        # Data input section
        data_frame = ttk.Frame(ops_frame)
        data_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(data_frame, text="Data (JSON):").pack(anchor=tk.W, padx=5)
        self.data_text = tk.Text(data_frame, height=10)
        self.data_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ID field
        id_frame = ttk.Frame(ops_frame)
        id_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(id_frame, text="ID:").pack(side=tk.LEFT, padx=5)
        self.id_var = tk.StringVar()
        id_entry = ttk.Entry(id_frame, textvariable=self.id_var, width=20)
        id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Operation buttons
        buttons_frame = ttk.Frame(ops_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Insert", command=self.insert_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Get", command=self.get_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Update", command=self.update_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Delete", command=self.delete_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Find All", command=self.find_all).pack(side=tk.LEFT, padx=5)
        
        # Blockchain verification
        verify_btn = ttk.Button(ops_frame, text="Verify Blockchain Integrity", command=self.verify_blockchain)
        verify_btn.pack(anchor=tk.E, pady=10, padx=5)
    
    def setup_api_tab(self):
        # API Configuration section
        config_frame = ttk.LabelFrame(self.api_tab, text="API Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        # Host and port
        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.host_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(config_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.port_var = tk.IntVar(value=8000)
        ttk.Entry(config_frame, textvariable=self.port_var, width=6).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # API Title and description
        ttk.Label(config_frame, text="API Title:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.title_var = tk.StringVar(value="IEDB API")
        ttk.Entry(config_frame, textvariable=self.title_var, width=30).grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(config_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.desc_var = tk.StringVar(value="Blockchain database API")
        ttk.Entry(config_frame, textvariable=self.desc_var, width=40).grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Security options
        security_frame = ttk.LabelFrame(self.api_tab, text="Security", padding="10")
        security_frame.pack(fill=tk.X, pady=10)
        
        self.enable_auth_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(security_frame, text="Enable Authentication", variable=self.enable_auth_var, command=self.toggle_auth_fields).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(security_frame, text="Secret Key:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.secret_var = tk.StringVar(value="supersecretkey")
        self.secret_entry = ttk.Entry(security_frame, textvariable=self.secret_var, width=30, state="disabled")
        self.secret_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(security_frame, text="User DB:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.user_db_var = tk.StringVar(value="users.json")
        self.user_db_entry = ttk.Entry(security_frame, textvariable=self.user_db_var, width=30, state="disabled")
        self.user_db_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Server control
        server_frame = ttk.LabelFrame(self.api_tab, text="API Server Control", padding="10")
        server_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(server_frame, text="Start API Server", command=self.start_api_server)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(server_frame, text="Stop API Server", command=self.stop_api_server, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.open_docs_button = ttk.Button(server_frame, text="Open Swagger Docs", command=self.open_swagger, state="disabled")
        self.open_docs_button.pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.LabelFrame(self.api_tab, text="Server Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.server_status_var = tk.StringVar(value="Server is not running")
        status_label = ttk.Label(status_frame, textvariable=self.server_status_var, font=('', 12))
        status_label.pack(pady=20)
    
    def setup_encryption_tab(self):
        # Encryption key management
        key_frame = ttk.LabelFrame(self.encryption_tab, text="Encryption Key Management", padding="10")
        key_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(key_frame, text="Keys Location:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.keys_path_var = tk.StringVar(value="./encryption_keys")
        keys_entry = ttk.Entry(key_frame, textvariable=self.keys_path_var, width=30)
        keys_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        browse_key_btn = ttk.Button(key_frame, text="Browse", command=self.browse_keys_path)
        browse_key_btn.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(key_frame, text="Initialize Encryption", command=self.init_encryption).grid(row=1, column=0, columnspan=3, padx=5, pady=10)
        
        # Key operations
        ops_key_frame = ttk.Frame(key_frame)
        ops_key_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(ops_key_frame, text="New Key Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.key_name_var = tk.StringVar()
        ttk.Entry(ops_key_frame, textvariable=self.key_name_var, width=20).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Button(ops_key_frame, text="Generate New Key", command=self.generate_key).grid(row=0, column=2, padx=5, pady=5)
        
        # Data encryption
        data_enc_frame = ttk.LabelFrame(self.encryption_tab, text="Data Encryption", padding="10")
        data_enc_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(data_enc_frame, text="Enter text to encrypt:").pack(anchor=tk.W, padx=5, pady=5)
        self.encrypt_text = tk.Text(data_enc_frame, height=4)
        self.encrypt_text.pack(fill=tk.X, padx=5, pady=5)
        
        button_frame = ttk.Frame(data_enc_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Encrypt", command=self.encrypt_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Decrypt", command=self.decrypt_data).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(data_enc_frame, text="Result:").pack(anchor=tk.W, padx=5, pady=5)
        self.result_text = tk.Text(data_enc_frame, height=6)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File encryption
        file_enc_frame = ttk.LabelFrame(self.encryption_tab, text="File Encryption", padding="10")
        file_enc_frame.pack(fill=tk.X, pady=10)
        
        file_buttons_frame = ttk.Frame(file_enc_frame)
        file_buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(file_buttons_frame, text="Encrypt File", command=self.encrypt_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_buttons_frame, text="Decrypt File", command=self.decrypt_file).pack(side=tk.LEFT, padx=5)
    
    def setup_about_tab(self):
        about_frame = ttk.Frame(self.about_tab, padding="20")
        about_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo or icon would go here
        
        title_label = ttk.Label(about_frame, text="IEDB - Integrated Encrypted Database", font=('', 16, 'bold'))
        title_label.pack(pady=10)
        
        version_label = ttk.Label(about_frame, text=f"Version {iedb.__version__}")
        version_label.pack()
        
        desc_label = ttk.Label(about_frame, text="A lightweight blockchain-based database with integrated encryption, \nauthentication, and REST API capabilities.", justify=tk.CENTER)
        desc_label.pack(pady=20)
        
        features_frame = ttk.LabelFrame(about_frame, text="Features", padding="10")
        features_frame.pack(fill=tk.X, pady=10)
        
        features = [
            "• Blockchain Database with integrity verification",
            "• Built-in encryption for sensitive data",
            "• JWT-based authentication",
            "• FastAPI integration for REST endpoints",
            "• Cross-platform compatibility"
        ]
        
        for feature in features:
            ttk.Label(features_frame, text=feature).pack(anchor=tk.W, pady=2)
        
        copyright_label = ttk.Label(about_frame, text="Copyright © 2023-2025 niranjoyy@gmail.com")
        copyright_label.pack(pady=20)
        
        license_label = ttk.Label(about_frame, text="Licensed under the GNU General Public License v3.0 (GPL-3.0)")
        license_label.pack()
    
    # Database tab methods
    def browse_db_path(self):
        path = filedialog.askdirectory(title="Select Database Location")
        if path:
            self.db_path_var.set(path)
    
    def create_db(self):
        path = self.db_path_var.get()
        if not path:
            messagebox.showerror("Error", "Please specify a database path")
            return
        
        try:
            self.db = BlockchainDB(path)
            self.db_path = path
            self.status_var.set(f"Database opened at {path}")
            messagebox.showinfo("Success", f"Database initialized at {path}")
            self.refresh_collections()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create database: {str(e)}")
    
    def refresh_collections(self):
        if not self.db:
            messagebox.showerror("Error", "Please open a database first")
            return
        
        try:
            collections = self.db.list_collections()
            self.collections_listbox.delete(0, tk.END)
            for coll in collections:
                self.collections_listbox.insert(tk.END, coll)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list collections: {str(e)}")
    
    def on_collection_select(self, event):
        if not self.collections_listbox.curselection():
            return
        
        selected_collection = self.collections_listbox.get(self.collections_listbox.curselection())
        self.collection_var.set(selected_collection)
    
    def insert_data(self):
        if not self.db:
            messagebox.showerror("Error", "Please open a database first")
            return
        
        collection = self.collection_var.get()
        if not collection:
            messagebox.showerror("Error", "Please specify a collection")
            return
        
        try:
            data_str = self.data_text.get("1.0", tk.END).strip()
            import json
            data = json.loads(data_str)
            
            # Use ID if provided, otherwise let the DB generate one
            doc_id = self.id_var.get()
            if doc_id:
                data["id"] = doc_id
            
            result_id = self.db.insert(collection, data)
            self.status_var.set(f"Inserted document with ID: {result_id}")
            messagebox.showinfo("Success", f"Document inserted with ID: {result_id}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON data")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to insert: {str(e)}")
    
    def get_data(self):
        if not self.db:
            messagebox.showerror("Error", "Please open a database first")
            return
        
        collection = self.collection_var.get()
        doc_id = self.id_var.get()
        
        if not collection or not doc_id:
            messagebox.showerror("Error", "Please specify both collection and ID")
            return
        
        try:
            result = self.db.get(collection, doc_id)
            if result:
                import json
                self.data_text.delete("1.0", tk.END)
                self.data_text.insert("1.0", json.dumps(result, indent=2))
                self.status_var.set(f"Retrieved document from {collection}")
            else:
                messagebox.showinfo("Not Found", f"No document found with ID {doc_id} in {collection}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve: {str(e)}")
    
    def update_data(self):
        if not self.db:
            messagebox.showerror("Error", "Please open a database first")
            return
        
        collection = self.collection_var.get()
        doc_id = self.id_var.get()
        
        if not collection or not doc_id:
            messagebox.showerror("Error", "Please specify both collection and ID")
            return
        
        try:
            data_str = self.data_text.get("1.0", tk.END).strip()
            import json
            data = json.loads(data_str)
            
            success = self.db.update(collection, doc_id, data)
            if success:
                self.status_var.set(f"Updated document in {collection}")
                messagebox.showinfo("Success", f"Document {doc_id} updated in {collection}")
            else:
                messagebox.showinfo("Not Found", f"No document found with ID {doc_id} to update")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON data")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update: {str(e)}")
    
    def delete_data(self):
        if not self.db:
            messagebox.showerror("Error", "Please open a database first")
            return
        
        collection = self.collection_var.get()
        doc_id = self.id_var.get()
        
        if not collection or not doc_id:
            messagebox.showerror("Error", "Please specify both collection and ID")
            return
        
        try:
            success = self.db.delete(collection, doc_id)
            if success:
                self.status_var.set(f"Deleted document from {collection}")
                messagebox.showinfo("Success", f"Document {doc_id} deleted from {collection}")
                # Clear the data text area
                self.data_text.delete("1.0", tk.END)
            else:
                messagebox.showinfo("Not Found", f"No document found with ID {doc_id} to delete")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    
    def find_all(self):
        if not self.db:
            messagebox.showerror("Error", "Please open a database first")
            return
        
        collection = self.collection_var.get()
        if not collection:
            messagebox.showerror("Error", "Please specify a collection")
            return
        
        try:
            results = self.db.find(collection, {})
            import json
            self.data_text.delete("1.0", tk.END)
            self.data_text.insert("1.0", json.dumps(results, indent=2))
            self.status_var.set(f"Found {len(results)} documents in {collection}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to find documents: {str(e)}")
    
    def verify_blockchain(self):
        if not self.db or not isinstance(self.db, BlockchainDB):
            messagebox.showerror("Error", "Please open a blockchain database first")
            return
        
        try:
            is_valid = self.db.verify_chain()
            if is_valid:
                messagebox.showinfo("Verification", "Blockchain integrity verified: All data is valid and unmodified")
                self.status_var.set("Blockchain integrity verified")
            else:
                messagebox.showwarning("Verification Failed", "Blockchain integrity check failed: Data may have been tampered with")
                self.status_var.set("Blockchain integrity verification FAILED")
        except Exception as e:
            messagebox.showerror("Error", f"Verification error: {str(e)}")
    
    # API tab methods
    def toggle_auth_fields(self):
        state = "normal" if self.enable_auth_var.get() else "disabled"
        self.secret_entry.config(state=state)
        self.user_db_entry.config(state=state)
    
    def start_api_server(self):
        if not self.db:
            messagebox.showerror("Error", "Please open a database first")
            return
        
        if self.api_running:
            messagebox.showinfo("Already Running", "API server is already running")
            return
        
        try:
            host = self.host_var.get()
            port = self.port_var.get()
            title = self.title_var.get()
            desc = self.desc_var.get()
            
            # Security setup
            security = None
            if self.enable_auth_var.get():
                secret_key = self.secret_var.get()
                user_db = self.user_db_var.get()
                
                auth = JWTAuth(secret_key=secret_key)
                security = SecurityManager(auth, user_db_path=user_db)
                
                # Ensure at least one user exists
                if not os.path.exists(user_db):
                    security.register_user("admin", "admin123")
                    messagebox.showinfo("User Created", "Default user created: admin/admin123")
            
            # Create API with or without security
            self.api = APIManager(
                database=self.db,
                security=security,
                title=title,
                description=desc
            )
            
            # Start server in a new thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                args=(host, port),
                daemon=True
            )
            self.server_thread.start()
            
            # Update UI
            self.api_running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.open_docs_button.config(state="normal")
            self.server_status_var.set(f"Server running at http://{host}:{port}")
            self.status_var.set(f"API server started on port {port}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start API server: {str(e)}")
    
    def _run_server(self, host, port):
        import uvicorn
        
        # Run with minimal output to avoid console clutter
        config = uvicorn.Config(
            app=self.api.app,
            host=host,
            port=port,
            log_level="warning"
        )
        server = uvicorn.Server(config)
        
        try:
            server.run()
        except Exception as e:
            # Update UI from the main thread
            self.root.after(0, lambda: self._handle_server_error(str(e)))
    
    def _handle_server_error(self, error_msg):
        self.api_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.open_docs_button.config(state="disabled")
        self.server_status_var.set(f"Server error: {error_msg}")
        messagebox.showerror("Server Error", f"API server error: {error_msg}")
    
    def stop_api_server(self):
        if not self.api_running:
            return
        
        # There's no clean way to stop uvicorn in a thread
        # This is a hack that will work for our demo
        self.api_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.open_docs_button.config(state="disabled")
        self.server_status_var.set("Server stopped")
        self.status_var.set("API server stopped")
        messagebox.showinfo("Server Stopped", "API server has been stopped")
    
    def open_swagger(self):
        if not self.api_running:
            messagebox.showerror("Error", "API server is not running")
            return
        
        host = self.host_var.get()
        port = self.port_var.get()
        url = f"http://{host}:{port}/docs"
        
        try:
            webbrowser.open(url)
            self.status_var.set("Opened Swagger documentation")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser: {str(e)}")
    
    # Encryption tab methods
    def browse_keys_path(self):
        path = filedialog.askdirectory(title="Select Encryption Keys Location")
        if path:
            self.keys_path_var.set(path)
    
    def init_encryption(self):
        keys_path = self.keys_path_var.get()
        if not keys_path:
            messagebox.showerror("Error", "Please specify a keys location")
            return
        
        try:
            self.enc = EncryptionManager(keys_path)
            messagebox.showinfo("Success", f"Encryption initialized with keys at {keys_path}")
            self.status_var.set("Encryption system initialized")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize encryption: {str(e)}")
    
    def generate_key(self):
        if not hasattr(self, 'enc'):
            messagebox.showerror("Error", "Please initialize encryption first")
            return
        
        key_name = self.key_name_var.get()
        if not key_name:
            messagebox.showerror("Error", "Please specify a key name")
            return
        
        try:
            self.enc.generate_key(key_name)
            messagebox.showinfo("Success", f"Key '{key_name}' generated successfully")
            self.status_var.set(f"Generated encryption key: {key_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate key: {str(e)}")
    
    def encrypt_data(self):
        if not hasattr(self, 'enc'):
            messagebox.showerror("Error", "Please initialize encryption first")
            return
        
        data = self.encrypt_text.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please enter data to encrypt")
            return
        
        try:
            encrypted = self.enc.encrypt_data(data)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", encrypted)
            self.status_var.set("Data encrypted")
        except Exception as e:
            messagebox.showerror("Error", f"Encryption failed: {str(e)}")
    
    def decrypt_data(self):
        if not hasattr(self, 'enc'):
            messagebox.showerror("Error", "Please initialize encryption first")
            return
        
        encrypted_data = self.encrypt_text.get("1.0", tk.END).strip()
        if not encrypted_data:
            messagebox.showerror("Error", "Please enter data to decrypt")
            return
        
        try:
            decrypted = self.enc.decrypt_data(encrypted_data)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", decrypted)
            self.status_var.set("Data decrypted")
        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")
    
    def encrypt_file(self):
        if not hasattr(self, 'enc'):
            messagebox.showerror("Error", "Please initialize encryption first")
            return
        
        source = filedialog.askopenfilename(title="Select File to Encrypt")
        if not source:
            return
        
        target = filedialog.asksaveasfilename(title="Save Encrypted File As", initialfile=f"{os.path.basename(source)}.enc")
        if not target:
            return
        
        try:
            self.enc.encrypt_file(source, target)
            messagebox.showinfo("Success", "File encrypted successfully")
            self.status_var.set(f"Encrypted file: {os.path.basename(source)}")
        except Exception as e:
            messagebox.showerror("Error", f"File encryption failed: {str(e)}")
    
    def decrypt_file(self):
        if not hasattr(self, 'enc'):
            messagebox.showerror("Error", "Please initialize encryption first")
            return
        
        source = filedialog.askopenfilename(title="Select Encrypted File")
        if not source:
            return
        
        target = filedialog.asksaveasfilename(title="Save Decrypted File As")
        if not target:
            return
        
        try:
            self.enc.decrypt_file(source, target)
            messagebox.showinfo("Success", "File decrypted successfully")
            self.status_var.set(f"Decrypted file: {os.path.basename(source)}")
        except Exception as e:
            messagebox.showerror("Error", f"File decryption failed: {str(e)}")

def main():
    root = tk.Tk()
    app = IEDBApp(root)
    
    # Set window icon if available
    # if os.path.exists("icon.ico"):
    #     root.iconbitmap("icon.ico")
    
    # Center the window on the screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
EOF

echo -e "${YELLOW}Creating Windows EXE package...${NC}"

# Create PyInstaller spec file
cat > "iedb_win.spec" << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['iedb_win_wrapper.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'fastapi', 'uvicorn', 'pydantic', 'starlette',
        'cryptography', 'python-jose', 'passlib',
        'iedb', 'iedb.core', 'iedb.api', 'iedb.security', 'iedb.encryption'
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
    name='IEDB_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
EOF

# Create a simple icon for the app
echo -e "${BLUE}Creating app icon...${NC}"
cat > "create_icon.py" << 'EOF'
from PIL import Image, ImageDraw

# Create a 256x256 pixel image with a transparent background
img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Draw a blue rounded rectangle
d.rounded_rectangle([(20, 20), (236, 236)], radius=30, fill=(41, 128, 185))

# Draw a white database cylinder
d.ellipse([(60, 70), (196, 110)], fill=(255, 255, 255))
d.rectangle([(60, 90), (196, 170)], fill=(255, 255, 255))
d.ellipse([(60, 150), (196, 190)], fill=(255, 255, 255))

# Draw lock symbol
d.rectangle([(98, 110), (158, 180)], fill=(41, 128, 185))
d.rectangle([(108, 80), (148, 120)], outline=(41, 128, 185), width=12)

# Save as icon
img.save('icon.ico', format='ICO')
EOF

# Create icon using Python
pip install pillow
python create_icon.py

# Build the Windows executable
echo -e "${YELLOW}Building Windows executable with PyInstaller...${NC}"
if command -v python3-wine &> /dev/null; then
    wine python3 -m PyInstaller iedb_win.spec
elif command -v wine &> /dev/null; then
    wine python -m PyInstaller iedb_win.spec
else
    # Fallback to local PyInstaller
    pip install pyinstaller
    pyinstaller iedb_win.spec
fi

# Check if build was successful
if [ -f "dist/IEDB_Manager.exe" ]; then
    echo -e "${GREEN}Windows EXE built successfully: dist/IEDB_Manager.exe${NC}"
else
    echo -e "${RED}Failed to build Windows EXE${NC}"
fi

# Create a ZIP file for Windows distribution
echo -e "${YELLOW}Creating ZIP package for Windows...${NC}"
if [ -d "dist" ]; then
    zip -r "iedb_windows.zip" dist/IEDB_Manager.exe
    echo -e "${GREEN}Created Windows ZIP package: iedb_windows.zip${NC}"
fi

echo -e "${GREEN}EXE package creation process completed.${NC}"
echo -e "${BLUE}The Windows executable is available in the dist/ directory${NC}"
echo -e "${YELLOW}You can distribute iedb_windows.zip to Windows users.${NC}"