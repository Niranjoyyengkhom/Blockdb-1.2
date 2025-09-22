"""
Self-Balancing B-Tree Implementation for Blockchain Database
Optimized for fast insertion, deletion, and query operations
"""

import json
import pickle
import threading
from typing import Any, Optional, List, Tuple, Dict, Iterator
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import os


@dataclass
class BTreeNode:
    """B-Tree node with keys, values, and child pointers"""
    is_leaf: bool = True
    keys: List[Any] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)  # For leaf nodes
    children: List['BTreeNode'] = field(default_factory=list)  # For internal nodes
    parent: Optional['BTreeNode'] = None
    node_id: str = field(default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16])
    
    def __post_init__(self):
        if not self.keys:
            self.keys = []
        if not self.values:
            self.values = []
        if not self.children:
            self.children = []


class BTreeEngine:
    """
    Self-Balancing B-Tree implementation optimized for database operations
    Features:
    - Configurable order (degree)
    - Thread-safe operations
    - Persistent storage
    - Range queries
    - Bulk operations
    - Memory-efficient design
    """
    
    def __init__(self, order: int = 100, storage_path: str = "btree_storage"):
        """
        Initialize B-Tree with specified order
        
        Args:
            order: Maximum number of children per node (degree)
            storage_path: Directory for persistent storage
        """
        self.order = order
        self.min_keys = order // 2
        self.max_keys = order - 1
        self.root: Optional[BTreeNode] = None
        self.storage_path = storage_path
        self.lock = threading.RLock()
        self.node_cache: Dict[str, BTreeNode] = {}
        self.cache_size_limit = 1000
        self.statistics = {
            'total_nodes': 0,
            'total_keys': 0,
            'height': 0,
            'insertions': 0,
            'deletions': 0,
            'searches': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize empty tree
        if not self.root:
            self.root = BTreeNode()
            self.statistics['total_nodes'] = 1
    
    def _save_node(self, node: BTreeNode) -> None:
        """Save node to persistent storage"""
        try:
            node_path = os.path.join(self.storage_path, f"node_{node.node_id}.pkl")
            with open(node_path, 'wb') as f:
                pickle.dump(node, f)
        except Exception as e:
            print(f"Error saving node {node.node_id}: {e}")
    
    def _load_node(self, node_id: str) -> Optional[BTreeNode]:
        """Load node from persistent storage"""
        try:
            node_path = os.path.join(self.storage_path, f"node_{node_id}.pkl")
            if os.path.exists(node_path):
                with open(node_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading node {node_id}: {e}")
        return None
    
    def _cache_node(self, node: BTreeNode) -> None:
        """Add node to memory cache"""
        if len(self.node_cache) >= self.cache_size_limit:
            # Remove oldest entry (simple LRU)
            oldest_key = next(iter(self.node_cache))
            del self.node_cache[oldest_key]
        
        self.node_cache[node.node_id] = node
    
    def _get_cached_node(self, node_id: str) -> Optional[BTreeNode]:
        """Get node from cache or load from storage"""
        if node_id in self.node_cache:
            self.statistics['cache_hits'] += 1
            return self.node_cache[node_id]
        
        self.statistics['cache_misses'] += 1
        node = self._load_node(node_id)
        if node:
            self._cache_node(node)
        return node
    
    def search(self, key: Any) -> Optional[Any]:
        """
        Search for a key in the B-Tree
        Time Complexity: O(log n)
        """
        with self.lock:
            self.statistics['searches'] += 1
            if self.root is None:
                return None
            return self._search_recursive(self.root, key)
    
    def _search_recursive(self, node: BTreeNode, key: Any) -> Optional[Any]:
        """Recursive search implementation"""
        if not node:
            return None
        
        # Find the appropriate position
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        # Check if key found
        if i < len(node.keys) and key == node.keys[i]:
            if node.is_leaf:
                return node.values[i] if i < len(node.values) else None
            else:
                # For internal nodes, continue search in right child
                return self._search_recursive(node.children[i + 1], key)
        
        # If leaf node and key not found
        if node.is_leaf:
            return None
        
        # Continue search in appropriate child
        if i < len(node.children):
            return self._search_recursive(node.children[i], key)
        
        return None
    
    def insert(self, key: Any, value: Any) -> bool:
        """
        Insert key-value pair into B-Tree
        Time Complexity: O(log n)
        """
        with self.lock:
            self.statistics['insertions'] += 1
            
            # Initialize root if it doesn't exist
            if self.root is None:
                self.root = BTreeNode(is_leaf=True)
                self.statistics['total_nodes'] += 1
            
            # Handle root split if necessary
            if len(self.root.keys) == self.max_keys:
                new_root = BTreeNode(is_leaf=False)
                new_root.children.append(self.root)
                self.root.parent = new_root
                self._split_child(new_root, 0)
                self.root = new_root
                self.statistics['total_nodes'] += 1
            
            result = self._insert_non_full(self.root, key, value)
            if result:
                self.statistics['total_keys'] += 1
                self._update_height()
            return result
    
    def _insert_non_full(self, node: BTreeNode, key: Any, value: Any) -> bool:
        """Insert into a node that is not full"""
        i = len(node.keys) - 1
        
        if node.is_leaf:
            # Insert into leaf node
            node.keys.append(None)
            node.values.append(None)
            
            # Shift elements to make space
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            
            # Insert the new key-value pair
            node.keys[i + 1] = key
            node.values[i + 1] = value
            
            # Save updated node
            self._save_node(node)
            self._cache_node(node)
            return True
        
        else:
            # Find child to insert into
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            # Split child if necessary
            if len(node.children[i].keys) == self.max_keys:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            
            return self._insert_non_full(node.children[i], key, value)
    
    def _split_child(self, parent: BTreeNode, index: int) -> None:
        """Split a full child node"""
        full_child = parent.children[index]
        new_child = BTreeNode(is_leaf=full_child.is_leaf)
        
        # Calculate split point
        mid_index = self.min_keys
        
        # Move half the keys to new node
        new_child.keys = full_child.keys[mid_index + 1:]
        full_child.keys = full_child.keys[:mid_index]
        
        if full_child.is_leaf:
            # Move corresponding values for leaf nodes
            new_child.values = full_child.values[mid_index + 1:]
            full_child.values = full_child.values[:mid_index]
        else:
            # Move children for internal nodes
            new_child.children = full_child.children[mid_index + 1:]
            full_child.children = full_child.children[:mid_index + 1]
            
            # Update parent pointers
            for child in new_child.children:
                child.parent = new_child
        
        # Set parent for new child
        new_child.parent = parent
        
        # Insert the middle key into parent
        parent.keys.insert(index, full_child.keys[mid_index])
        parent.children.insert(index + 1, new_child)
        
        # Update statistics
        self.statistics['total_nodes'] += 1
        
        # Save updated nodes
        self._save_node(full_child)
        self._save_node(new_child)
        self._save_node(parent)
        
        # Update cache
        self._cache_node(full_child)
        self._cache_node(new_child)
        self._cache_node(parent)
    
    def delete(self, key: Any) -> bool:
        """
        Delete a key from the B-Tree
        Time Complexity: O(log n)
        """
        with self.lock:
            self.statistics['deletions'] += 1
            
            # Check if root exists
            if self.root is None:
                return False
                
            result = self._delete_recursive(self.root, key)
            
            # Handle empty root
            if self.root is not None and len(self.root.keys) == 0 and not self.root.is_leaf:
                self.root = self.root.children[0]
                self.root.parent = None
                self.statistics['total_nodes'] -= 1
            
            if result:
                self.statistics['total_keys'] -= 1
                self._update_height()
            
            return result
    
    def _delete_recursive(self, node: BTreeNode, key: Any) -> bool:
        """Recursive delete implementation"""
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if i < len(node.keys) and key == node.keys[i]:
            # Key found
            if node.is_leaf:
                # Delete from leaf
                node.keys.pop(i)
                node.values.pop(i)
                self._save_node(node)
                return True
            else:
                # Delete from internal node
                return self._delete_internal_node(node, i)
        
        elif node.is_leaf:
            # Key not found in leaf
            return False
        
        else:
            # Key not in this node, go to appropriate child
            flag = (i == len(node.keys))
            
            # Ensure child has enough keys
            if len(node.children[i].keys) < self.min_keys:
                self._fix_child(node, i)
            
            # The key to delete may now be in the merged child
            if flag and i > len(node.keys):
                return self._delete_recursive(node.children[i - 1], key)
            else:
                return self._delete_recursive(node.children[i], key)
    
    def _delete_internal_node(self, node: BTreeNode, index: int) -> bool:
        """Delete key from internal node"""
        key = node.keys[index]
        
        # Case 1: Left child has enough keys
        if len(node.children[index].keys) >= self.min_keys:
            predecessor = self._get_predecessor(node, index)
            node.keys[index] = predecessor[0]
            return self._delete_recursive(node.children[index], predecessor[0])
        
        # Case 2: Right child has enough keys
        elif len(node.children[index + 1].keys) >= self.min_keys:
            successor = self._get_successor(node, index)
            node.keys[index] = successor[0]
            return self._delete_recursive(node.children[index + 1], successor[0])
        
        # Case 3: Both children have minimum keys
        else:
            self._merge_children(node, index)
            return self._delete_recursive(node.children[index], key)
    
    def _get_predecessor(self, node: BTreeNode, index: int) -> Tuple[Any, Any]:
        """Get predecessor key-value pair"""
        current = node.children[index]
        while not current.is_leaf:
            current = current.children[-1]
        return (current.keys[-1], current.values[-1] if current.values else None)
    
    def _get_successor(self, node: BTreeNode, index: int) -> Tuple[Any, Any]:
        """Get successor key-value pair"""
        current = node.children[index + 1]
        while not current.is_leaf:
            current = current.children[0]
        return (current.keys[0], current.values[0] if current.values else None)
    
    def _fix_child(self, node: BTreeNode, index: int) -> None:
        """Fix child that has too few keys"""
        # Try borrowing from left sibling
        if index != 0 and len(node.children[index - 1].keys) >= self.min_keys:
            self._borrow_from_left(node, index)
        
        # Try borrowing from right sibling
        elif index != len(node.children) - 1 and len(node.children[index + 1].keys) >= self.min_keys:
            self._borrow_from_right(node, index)
        
        # Merge with sibling
        else:
            if index != len(node.children) - 1:
                self._merge_children(node, index)
            else:
                self._merge_children(node, index - 1)
    
    def _borrow_from_left(self, node: BTreeNode, index: int) -> None:
        """Borrow a key from left sibling"""
        child = node.children[index]
        sibling = node.children[index - 1]
        
        # Move key from parent to child
        child.keys.insert(0, node.keys[index - 1])
        if child.is_leaf and child.values:
            child.values.insert(0, None)  # Placeholder
        
        # Move key from sibling to parent
        node.keys[index - 1] = sibling.keys[-1]
        sibling.keys.pop()
        
        if child.is_leaf and sibling.values:
            if child.values:
                child.values[0] = sibling.values[-1]
            sibling.values.pop()
        
        # Move child pointer if not leaf
        if not child.is_leaf:
            child.children.insert(0, sibling.children[-1])
            sibling.children.pop()
            child.children[0].parent = child
        
        # Save updated nodes
        self._save_node(child)
        self._save_node(sibling)
        self._save_node(node)
    
    def _borrow_from_right(self, node: BTreeNode, index: int) -> None:
        """Borrow a key from right sibling"""
        child = node.children[index]
        sibling = node.children[index + 1]
        
        # Move key from parent to child
        child.keys.append(node.keys[index])
        if child.is_leaf and child.values:
            child.values.append(None)  # Placeholder
        
        # Move key from sibling to parent
        node.keys[index] = sibling.keys[0]
        sibling.keys.pop(0)
        
        if child.is_leaf and sibling.values:
            if child.values:
                child.values[-1] = sibling.values[0]
            sibling.values.pop(0)
        
        # Move child pointer if not leaf
        if not child.is_leaf:
            child.children.append(sibling.children[0])
            sibling.children.pop(0)
            child.children[-1].parent = child
        
        # Save updated nodes
        self._save_node(child)
        self._save_node(sibling)
        self._save_node(node)
    
    def _merge_children(self, node: BTreeNode, index: int) -> None:
        """Merge child with its sibling"""
        child = node.children[index]
        sibling = node.children[index + 1]
        
        # Move key from parent to child
        child.keys.append(node.keys[index])
        
        # Move all keys from sibling to child
        child.keys.extend(sibling.keys)
        
        if child.is_leaf:
            if child.values and sibling.values:
                child.values.extend(sibling.values)
        else:
            # Move children pointers
            child.children.extend(sibling.children)
            for grandchild in sibling.children:
                grandchild.parent = child
        
        # Remove key and sibling from parent
        node.keys.pop(index)
        node.children.pop(index + 1)
        
        # Update statistics
        self.statistics['total_nodes'] -= 1
        
        # Save updated nodes
        self._save_node(child)
        self._save_node(node)
        
        # Remove sibling from storage
        sibling_path = os.path.join(self.storage_path, f"node_{sibling.node_id}.pkl")
        if os.path.exists(sibling_path):
            os.remove(sibling_path)
    
    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        """
        Perform range query to get all key-value pairs in range [start_key, end_key]
        Time Complexity: O(log n + k) where k is the number of results
        """
        with self.lock:
            result = []
            if self.root is not None:
                self._range_query_recursive(self.root, start_key, end_key, result)
            return result
    
    def _range_query_recursive(self, node: BTreeNode, start_key: Any, end_key: Any, result: List[Tuple[Any, Any]]) -> None:
        """Recursive range query implementation"""
        if not node:
            return
        
        i = 0
        while i < len(node.keys):
            # If this is a leaf node, check the key
            if node.is_leaf:
                if start_key <= node.keys[i] <= end_key:
                    value = node.values[i] if i < len(node.values) else None
                    result.append((node.keys[i], value))
            else:
                # For internal nodes, recursively search children
                if node.keys[i] < start_key:
                    pass  # Skip this subtree
                elif node.keys[i] > end_key:
                    # Search left child and stop
                    if i < len(node.children):
                        self._range_query_recursive(node.children[i], start_key, end_key, result)
                    break
                else:
                    # Key is in range, search left child
                    if i < len(node.children):
                        self._range_query_recursive(node.children[i], start_key, end_key, result)
            
            i += 1
        
        # Search the rightmost child for internal nodes
        if not node.is_leaf and i < len(node.children):
            self._range_query_recursive(node.children[i], start_key, end_key, result)
    
    def bulk_insert(self, items: List[Tuple[Any, Any]]) -> int:
        """
        Bulk insert multiple key-value pairs
        Returns number of successfully inserted items
        """
        with self.lock:
            success_count = 0
            # Sort items by key for better insertion performance
            sorted_items = sorted(items, key=lambda x: x[0])
            
            for key, value in sorted_items:
                if self.insert(key, value):
                    success_count += 1
            
            return success_count
    
    def _update_height(self) -> None:
        """Update tree height statistics"""
        if not self.root:
            self.statistics['height'] = 0
            return
        
        height = 0
        current = self.root
        while not current.is_leaf:
            height += 1
            if current.children:
                current = current.children[0]
            else:
                break
        
        self.statistics['height'] = height
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed B-Tree statistics"""
        with self.lock:
            self._update_height()
            return {
                **self.statistics,
                'order': self.order,
                'min_keys_per_node': self.min_keys,
                'max_keys_per_node': self.max_keys,
                'cache_size': len(self.node_cache),
                'cache_hit_ratio': (
                    self.statistics['cache_hits'] / 
                    (self.statistics['cache_hits'] + self.statistics['cache_misses'])
                    if (self.statistics['cache_hits'] + self.statistics['cache_misses']) > 0 else 0
                ),
                'average_keys_per_node': (
                    self.statistics['total_keys'] / self.statistics['total_nodes']
                    if self.statistics['total_nodes'] > 0 else 0
                )
            }
    
    def optimize(self) -> Dict[str, Any]:
        """Optimize B-Tree structure and return optimization report"""
        with self.lock:
            optimization_report = {
                'nodes_before': self.statistics['total_nodes'],
                'keys_before': self.statistics['total_keys'],
                'height_before': self.statistics['height'],
                'cache_cleared': len(self.node_cache),
                'optimizations_applied': []
            }
            
            # Clear cache to free memory
            self.node_cache.clear()
            optimization_report['optimizations_applied'].append('cache_cleared')
            
            # Update statistics
            self._update_height()
            
            optimization_report.update({
                'nodes_after': self.statistics['total_nodes'],
                'keys_after': self.statistics['total_keys'],
                'height_after': self.statistics['height']
            })
            
            return optimization_report
    
    def iterate_all(self) -> Iterator[Tuple[Any, Any]]:
        """Iterate through all key-value pairs in sorted order"""
        with self.lock:
            if self.root is not None:
                yield from self._iterate_recursive(self.root)
    
    def _iterate_recursive(self, node: BTreeNode) -> Iterator[Tuple[Any, Any]]:
        """Recursive iteration implementation"""
        if not node:
            return
        
        if node.is_leaf:
            # Yield all key-value pairs from leaf
            for i in range(len(node.keys)):
                value = node.values[i] if i < len(node.values) else None
                yield (node.keys[i], value)
        else:
            # For internal nodes, iterate through children and keys
            for i in range(len(node.keys)):
                # Iterate left child
                if i < len(node.children):
                    yield from self._iterate_recursive(node.children[i])
            
            # Iterate rightmost child
            if len(node.children) > len(node.keys):
                yield from self._iterate_recursive(node.children[-1])
    
    def close(self) -> None:
        """Close B-Tree and save all cached nodes"""
        with self.lock:
            # Save all cached nodes
            for node in self.node_cache.values():
                self._save_node(node)
            
            # Save tree metadata
            metadata = {
                'order': self.order,
                'root_id': self.root.node_id if self.root else None,
                'statistics': self.statistics
            }
            
            metadata_path = os.path.join(self.storage_path, 'btree_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Clear cache
            self.node_cache.clear()
    
    def load_from_storage(self) -> bool:
        """Load B-Tree from persistent storage"""
        try:
            metadata_path = os.path.join(self.storage_path, 'btree_metadata.json')
            if not os.path.exists(metadata_path):
                return False
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.order = metadata.get('order', self.order)
            self.statistics = metadata.get('statistics', self.statistics)
            
            root_id = metadata.get('root_id')
            if root_id:
                self.root = self._load_node(root_id)
                if self.root:
                    self._cache_node(self.root)
                    return True
            
            return False
        
        except Exception as e:
            print(f"Error loading B-Tree from storage: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Create B-Tree with order 100 for optimal performance
    btree = BTreeEngine(order=100, storage_path="test_btree_storage")
    
    # Test insertions
    print("Testing B-Tree insertions...")
    test_data = [(i, f"value_{i}") for i in range(1000)]
    inserted = btree.bulk_insert(test_data)
    print(f"Inserted {inserted} items")
    
    # Test searches
    print("\nTesting searches...")
    for i in [100, 500, 999]:
        result = btree.search(i)
        print(f"Search key {i}: {result}")
    
    # Test range queries
    print("\nTesting range queries...")
    range_results = btree.range_query(450, 460)
    print(f"Range query [450, 460]: {range_results}")
    
    # Show statistics
    print("\nB-Tree Statistics:")
    stats = btree.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test optimization
    print("\nOptimizing B-Tree...")
    opt_report = btree.optimize()
    print(f"Optimization report: {opt_report}")
    
    # Close and save
    btree.close()
    print("\nB-Tree saved to storage")
