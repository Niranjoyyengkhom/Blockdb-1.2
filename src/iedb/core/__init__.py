"""
IEDB Core module - Main database functionality
"""
from typing import Dict, List, Any, Optional
import os
import json
import time


class Database:
    """Base database class for IEDB."""
    
    def __init__(self, path: str, name: str):
        """Initialize a new database.
        
        Args:
            path: Path where the database files will be stored
            name: Name of the database
        """
        self.path = path
        self.name = name
        self.data_dir = os.path.join(path, name)
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def create_collection(self, collection_name: str) -> bool:
        """Create a new collection in the database.
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            True if successful, False otherwise
        """
        collection_path = os.path.join(self.data_dir, f"{collection_name}.json")
        if os.path.exists(collection_path):
            return False
        
        with open(collection_path, "w") as f:
            json.dump([], f)
        
        return True
    
    def insert(self, collection_name: str, data: Dict[str, Any]) -> str:
        """Insert data into a collection.
        
        Args:
            collection_name: Name of the collection
            data: Data to insert
        
        Returns:
            ID of the inserted document
        """
        collection_path = os.path.join(self.data_dir, f"{collection_name}.json")
        if not os.path.exists(collection_path):
            self.create_collection(collection_name)
        
        try:
            with open(collection_path, "r") as f:
                collection_data = json.load(f)
        except json.JSONDecodeError:
            collection_data = []
        
        # Add document ID and timestamp
        if "_id" not in data:
            data["_id"] = f"{int(time.time())}_{len(collection_data)}"
        
        data["timestamp"] = int(time.time())
        
        collection_data.append(data)
        
        with open(collection_path, "w") as f:
            json.dump(collection_data, f, indent=2)
        
        return data["_id"]
    
    def find(self, collection_name: str, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find documents in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query conditions (optional)
        
        Returns:
            List of matching documents
        """
        collection_path = os.path.join(self.data_dir, f"{collection_name}.json")
        if not os.path.exists(collection_path):
            return []
        
        with open(collection_path, "r") as f:
            collection_data = json.load(f)
        
        if not query:
            return collection_data
        
        # Simple query filtering
        results = []
        for doc in collection_data:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            
            if match:
                results.append(doc)
        
        return results
    
    def update(self, collection_name: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in a collection.
        
        Args:
            collection_name: Name of the collection
            doc_id: ID of the document
            data: Updated data
        
        Returns:
            True if successful, False otherwise
        """
        collection_path = os.path.join(self.data_dir, f"{collection_name}.json")
        if not os.path.exists(collection_path):
            return False
        
        with open(collection_path, "r") as f:
            collection_data = json.load(f)
        
        for i, doc in enumerate(collection_data):
            if doc.get("_id") == doc_id:
                # Update document
                data["_id"] = doc_id
                data["timestamp"] = int(time.time())
                collection_data[i] = data
                
                with open(collection_path, "w") as f:
                    json.dump(collection_data, f, indent=2)
                
                return True
        
        return False
    
    def delete(self, collection_name: str, doc_id: str) -> bool:
        """Delete a document from a collection.
        
        Args:
            collection_name: Name of the collection
            doc_id: ID of the document
        
        Returns:
            True if successful, False otherwise
        """
        collection_path = os.path.join(self.data_dir, f"{collection_name}.json")
        if not os.path.exists(collection_path):
            return False
        
        with open(collection_path, "r") as f:
            collection_data = json.load(f)
        
        for i, doc in enumerate(collection_data):
            if doc.get("_id") == doc_id:
                # Remove document
                collection_data.pop(i)
                
                with open(collection_path, "w") as f:
                    json.dump(collection_data, f, indent=2)
                
                return True
        
        return False


class BlockchainDB(Database):
    """BlockchainDB with blockchain-inspired features."""
    
    def __init__(self, path: str, name: str):
        super().__init__(path, name)
        self.blockchain_file = os.path.join(self.data_dir, "blockchain.json")
        
        # Initialize blockchain if it doesn't exist
        if not os.path.exists(self.blockchain_file):
            genesis_block = {
                "index": 0,
                "timestamp": int(time.time()),
                "data": "Genesis Block",
                "previous_hash": "0",
                "hash": self._calculate_hash(0, "0", "Genesis Block")
            }
            
            with open(self.blockchain_file, "w") as f:
                json.dump([genesis_block], f, indent=2)
    
    def _calculate_hash(self, index: int, prev_hash: str, data: str) -> str:
        """Calculate a simple hash for the block.
        
        Args:
            index: Block index
            prev_hash: Previous block hash
            data: Block data
        
        Returns:
            Hash value as string
        """
        # Simple hash calculation (in real impl. use cryptography)
        import hashlib
        value = f"{index}{prev_hash}{data}{time.time()}"
        return hashlib.sha256(value.encode()).hexdigest()
    
    def add_block(self, data: Any) -> Dict[str, Any]:
        """Add a new block to the blockchain.
        
        Args:
            data: Data to store in the block
        
        Returns:
            The created block
        """
        with open(self.blockchain_file, "r") as f:
            blockchain = json.load(f)
        
        last_block = blockchain[-1]
        new_block = {
            "index": last_block["index"] + 1,
            "timestamp": int(time.time()),
            "data": data,
            "previous_hash": last_block["hash"],
            "hash": ""
        }
        
        # Calculate hash
        new_block["hash"] = self._calculate_hash(
            new_block["index"], 
            new_block["previous_hash"], 
            str(new_block["data"])
        )
        
        blockchain.append(new_block)
        
        with open(self.blockchain_file, "w") as f:
            json.dump(blockchain, f, indent=2)
        
        return new_block
    
    def verify_blockchain(self) -> bool:
        """Verify the integrity of the blockchain.
        
        Returns:
            True if the blockchain is valid, False otherwise
        """
        with open(self.blockchain_file, "r") as f:
            blockchain = json.load(f)
        
        for i in range(1, len(blockchain)):
            current_block = blockchain[i]
            previous_block = blockchain[i-1]
            
            # Verify hash connection
            if current_block["previous_hash"] != previous_block["hash"]:
                return False
            
            # Verify block hash
            calculated_hash = self._calculate_hash(
                current_block["index"],
                current_block["previous_hash"],
                str(current_block["data"])
            )
            if calculated_hash != current_block["hash"]:
                return False
        
        return True
    
    def get_blocks(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get blocks from the blockchain.
        
        Args:
            count: Number of recent blocks to retrieve (optional)
        
        Returns:
            List of blocks
        """
        with open(self.blockchain_file, "r") as f:
            blockchain = json.load(f)
        
        if count is None or count > len(blockchain):
            return blockchain
        
        return blockchain[-count:]