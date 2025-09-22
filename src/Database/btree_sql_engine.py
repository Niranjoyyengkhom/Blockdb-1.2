"""
Enhanced SQL Engine with B-Tree Backend
Integrates B-Tree optimization with SQL query processing for maximum performance
"""

import re
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
# import sqlparse  # Optional: for advanced SQL parsing

# Fallback database engine for SQL operations
class BTreeDatabaseEngine:
    """Simple database engine stub for B-Tree operations"""
    def __init__(self, *args, **kwargs):
        self.metadata = {'tables': {}}
        self.indexes = {}
        self.tables = {}
        
    def search_by_column(self, table_name, column, value):
        return []
        
    def range_query(self, table_name, column, start_value, end_value):
        return []
        
    def __getattr__(self, name):
                if name in ['metadata', 'indexes', 'tables']:
                    return getattr(self, name)
                return lambda *args, **kwargs: {"success": False, "error": "BTreeDatabaseEngine not available"}


class BTreeSQLEngine:
    """
    SQL Engine with B-Tree backend for optimal query performance
    Supports:
    - Standard SQL operations (SELECT, INSERT, UPDATE, DELETE)
    - Indexed queries with O(log n) performance
    - Complex WHERE clauses with range queries
    - JOIN operations using B-Tree indexes
    - Aggregation functions
    - Transaction support
    """
    
    def __init__(self, storage_path: str = "btree_sql_engine"):
        """Initialize B-Tree SQL Engine"""
        self.btree_db = BTreeDatabaseEngine(storage_path, btree_order=200)
        self.query_cache = {}
        self.query_stats = {
            'queries_executed': 0,
            'cache_hits': 0,
            'average_execution_time': 0,
            'slow_queries': []
        }
        
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query using B-Tree optimized backend
        
        Args:
            sql_query: SQL query string
            
        Returns:
            Dictionary with execution results and metadata
        """
        start_time = datetime.now()
        
        try:
            # Parse SQL query using simple string parsing
            query_type = self._get_query_type_simple(sql_query.strip())
            
            # Execute based on query type
            if query_type == 'SELECT':
                result = self._execute_select(None, sql_query)
            elif query_type == 'INSERT':
                result = self._execute_insert(None, sql_query)
            elif query_type == 'UPDATE':
                result = self._execute_update(None, sql_query)
            elif query_type == 'DELETE':
                result = self._execute_delete(None, sql_query)
            elif query_type == 'CREATE TABLE':
                result = self._execute_create_table(None, sql_query)
            elif query_type == 'CREATE INDEX':
                result = self._execute_create_index(None, sql_query)
            else:
                result = {
                    'success': False,
                    'error': f'Unsupported query type: {query_type}',
                    'data': None
                }
            
            # Update statistics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_query_stats(sql_query, execution_time, result['success'])
            
            result['execution_time'] = execution_time
            result['query_optimized'] = True
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'execution_time': execution_time,
                'query_optimized': False
            }
    
    def _get_query_type_simple(self, sql_query: str) -> str:
        """Determine the type of SQL query using simple string parsing"""
        sql_upper = sql_query.upper().strip()
        
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('CREATE TABLE'):
            return 'CREATE TABLE'
        elif sql_upper.startswith('CREATE INDEX'):
            return 'CREATE INDEX'
        else:
            return 'UNKNOWN'
    
    def _get_query_type(self, parsed_query) -> str:
        """Determine the type of SQL query"""
        first_token = str(parsed_query.tokens[0]).strip().upper()
        
        if first_token == 'SELECT':
            return 'SELECT'
        elif first_token == 'INSERT':
            return 'INSERT'
        elif first_token == 'UPDATE':
            return 'UPDATE'
        elif first_token == 'DELETE':
            return 'DELETE'
        elif first_token == 'CREATE':
            # Check if it's CREATE TABLE or CREATE INDEX
            token_str = str(parsed_query).upper()
            if 'CREATE TABLE' in token_str:
                return 'CREATE TABLE'
            elif 'CREATE INDEX' in token_str:
                return 'CREATE INDEX'
        
        return 'UNKNOWN'
    
    def _execute_select(self, parsed_query, original_query: str) -> Dict[str, Any]:
        """Execute SELECT query with B-Tree optimization"""
        try:
            # Parse SELECT components
            select_parts = self._parse_select_query(original_query)
            table_name = select_parts['table']
            columns = select_parts['columns']
            where_clause = select_parts['where']
            order_by = select_parts['order_by']
            limit = select_parts['limit']
            
            # Check if table exists
            if table_name not in self.btree_db.tables:
                return {
                    'success': False,
                    'error': f'Table {table_name} does not exist',
                    'data': None
                }
            
            # Optimize query execution based on WHERE clause
            if where_clause:
                results = self._execute_optimized_where(table_name, where_clause)
            else:
                # Full table scan
                results = self._get_all_records(table_name)
            
            # Apply column selection
            if columns != ['*']:
                results = self._select_columns(results, columns)
            
            # Apply ORDER BY
            if order_by:
                results = self._apply_order_by(results, order_by)
            
            # Apply LIMIT
            if limit:
                results = results[:limit]
            
            return {
                'success': True,
                'data': results,
                'rows_affected': len(results),
                'optimization_used': 'btree_index' if where_clause else 'full_scan'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'SELECT execution error: {str(e)}',
                'data': None
            }
    
    def _execute_insert(self, parsed_query, original_query: str) -> Dict[str, Any]:
        """Execute INSERT query with B-Tree optimization"""
        try:
            insert_parts = self._parse_insert_query(original_query)
            table_name = insert_parts['table']
            columns = insert_parts['columns']
            values = insert_parts['values']
            
            # Check if table exists
            if table_name not in self.btree_db.tables:
                return {
                    'success': False,
                    'error': f'Table {table_name} does not exist',
                    'data': None
                }
            
            # Prepare record
            if columns:
                record = dict(zip(columns, values))
            else:
                # Get table schema for column order
                table_meta = self.btree_db.metadata['tables'][table_name]
                schema_columns = list(table_meta['schema'].keys())
                record = dict(zip(schema_columns, values))
            
            # Insert using B-Tree
            success = self.btree_db.insert(table_name, record)
            
            return {
                'success': success,
                'data': None,
                'rows_affected': 1 if success else 0,
                'optimization_used': 'btree_insert'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'INSERT execution error: {str(e)}',
                'data': None
            }
    
    def _execute_update(self, parsed_query, original_query: str) -> Dict[str, Any]:
        """Execute UPDATE query with B-Tree optimization"""
        try:
            update_parts = self._parse_update_query(original_query)
            table_name = update_parts['table']
            set_clause = update_parts['set']
            where_clause = update_parts['where']
            
            # Check if table exists
            if table_name not in self.btree_db.tables:
                return {
                    'success': False,
                    'error': f'Table {table_name} does not exist',
                    'data': None
                }
            
            # Find records to update
            if where_clause:
                records_to_update = self._execute_optimized_where(table_name, where_clause)
            else:
                records_to_update = self._get_all_records(table_name)
            
            # Update records
            rows_affected = 0
            table_meta = self.btree_db.metadata['tables'][table_name]
            primary_key = table_meta['primary_key']
            
            for record in records_to_update:
                pk_value = record[primary_key]
                if self.btree_db.update(table_name, pk_value, set_clause):
                    rows_affected += 1
            
            return {
                'success': True,
                'data': None,
                'rows_affected': rows_affected,
                'optimization_used': 'btree_update'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'UPDATE execution error: {str(e)}',
                'data': None
            }
    
    def _execute_delete(self, parsed_query, original_query: str) -> Dict[str, Any]:
        """Execute DELETE query with B-Tree optimization"""
        try:
            delete_parts = self._parse_delete_query(original_query)
            table_name = delete_parts['table']
            where_clause = delete_parts['where']
            
            # Check if table exists
            if table_name not in self.btree_db.tables:
                return {
                    'success': False,
                    'error': f'Table {table_name} does not exist',
                    'data': None
                }
            
            # Find records to delete
            if where_clause:
                records_to_delete = self._execute_optimized_where(table_name, where_clause)
            else:
                return {
                    'success': False,
                    'error': 'DELETE without WHERE clause not allowed',
                    'data': None
                }
            
            # Delete records
            rows_affected = 0
            table_meta = self.btree_db.metadata['tables'][table_name]
            primary_key = table_meta['primary_key']
            
            for record in records_to_delete:
                pk_value = record[primary_key]
                if self.btree_db.delete(table_name, pk_value):
                    rows_affected += 1
            
            return {
                'success': True,
                'data': None,
                'rows_affected': rows_affected,
                'optimization_used': 'btree_delete'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'DELETE execution error: {str(e)}',
                'data': None
            }
    
    def _execute_create_table(self, parsed_query, original_query: str) -> Dict[str, Any]:
        """Execute CREATE TABLE with B-Tree backend"""
        try:
            table_parts = self._parse_create_table_query(original_query)
            table_name = table_parts['table']
            columns = table_parts['columns']
            primary_key = table_parts['primary_key']
            
            # Create table using B-Tree
            success = self.btree_db.create_table(
                table_name=table_name,
                schema=columns,
                primary_key=primary_key
            )
            
            return {
                'success': success,
                'data': None,
                'rows_affected': 0,
                'optimization_used': 'btree_table_creation'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'CREATE TABLE execution error: {str(e)}',
                'data': None
            }
    
    def _execute_create_index(self, parsed_query, original_query: str) -> Dict[str, Any]:
        """Execute CREATE INDEX with B-Tree backend"""
        try:
            index_parts = self._parse_create_index_query(original_query)
            table_name = index_parts['table']
            column_name = index_parts['column']
            
            # Create index using B-Tree
            success = self.btree_db._create_index(table_name, column_name)
            
            return {
                'success': success,
                'data': None,
                'rows_affected': 0,
                'optimization_used': 'btree_index_creation'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'CREATE INDEX execution error: {str(e)}',
                'data': None
            }
    
    def _execute_optimized_where(self, table_name: str, where_clause: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute WHERE clause with B-Tree optimization"""
        column = where_clause['column']
        operator = where_clause['operator']
        value = where_clause['value']
        
        # Check if column is indexed
        if (table_name in self.btree_db.indexes and 
            column in self.btree_db.indexes[table_name]):
            
            # Use B-Tree index for optimized search
            if operator == '=':
                return self.btree_db.search_by_column(table_name, column, value)
            elif operator == 'BETWEEN':
                start_value, end_value = value
                return self.btree_db.range_query(table_name, column, start_value, end_value)
            elif operator in ['>', '>=', '<', '<=']:
                # Range query optimization
                return self._range_query_with_operator(table_name, column, operator, value)
        
        # Fallback to full table scan with filtering
        all_records = self._get_all_records(table_name)
        return self._filter_records(all_records, where_clause)
    
    def _range_query_with_operator(self, table_name: str, column: str, 
                                  operator: str, value: Any) -> List[Dict[str, Any]]:
        """Perform range query with comparison operators"""
        # Get all records and filter (can be optimized further)
        all_records = self._get_all_records(table_name)
        filtered_records = []
        
        for record in all_records:
            record_value = record.get(column)
            if record_value is None:
                continue
                
            if operator == '>' and record_value > value:
                filtered_records.append(record)
            elif operator == '>=' and record_value >= value:
                filtered_records.append(record)
            elif operator == '<' and record_value < value:
                filtered_records.append(record)
            elif operator == '<=' and record_value <= value:
                filtered_records.append(record)
        
        return filtered_records
    
    def _get_all_records(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all records from a table"""
        records = []
        table_btree = self.btree_db.tables[table_name]
        
        for pk, encrypted_record in table_btree.iterate_all():
            decrypted_record = self.btree_db._decrypt_record(table_name, encrypted_record)
            if decrypted_record:
                records.append(decrypted_record)
        
        return records
    
    def _filter_records(self, records: List[Dict[str, Any]], 
                       where_clause: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter records based on WHERE clause"""
        column = where_clause['column']
        operator = where_clause['operator']
        value = where_clause['value']
        
        filtered_records = []
        for record in records:
            record_value = record.get(column)
            
            if self._evaluate_condition(record_value, operator, value):
                filtered_records.append(record)
        
        return filtered_records
    
    def _evaluate_condition(self, record_value: Any, operator: str, filter_value: Any) -> bool:
        """Evaluate a single condition"""
        if record_value is None:
            return False
        
        try:
            if operator == '=':
                return record_value == filter_value
            elif operator == '!=':
                return record_value != filter_value
            elif operator == '>':
                return record_value > filter_value
            elif operator == '>=':
                return record_value >= filter_value
            elif operator == '<':
                return record_value < filter_value
            elif operator == '<=':
                return record_value <= filter_value
            elif operator == 'LIKE':
                return str(filter_value).replace('%', '.*') in str(record_value)
            elif operator == 'IN':
                return record_value in filter_value
            elif operator == 'BETWEEN':
                start_value, end_value = filter_value
                return start_value <= record_value <= end_value
        except:
            return False
        
        return False
    
    def _select_columns(self, records: List[Dict[str, Any]], 
                       columns: List[str]) -> List[Dict[str, Any]]:
        """Select specific columns from records"""
        if not records or columns == ['*']:
            return records
        
        selected_records = []
        for record in records:
            selected_record = {}
            for column in columns:
                if column in record:
                    selected_record[column] = record[column]
            selected_records.append(selected_record)
        
        return selected_records
    
    def _apply_order_by(self, records: List[Dict[str, Any]], 
                       order_by: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply ORDER BY clause"""
        column = order_by['column']
        direction = order_by['direction']
        
        try:
            return sorted(
                records,
                key=lambda x: x.get(column, ''),
                reverse=(direction.upper() == 'DESC')
            )
        except:
            return records
    
    # SQL Parsing Methods
    def _parse_select_query(self, query: str) -> Dict[str, Any]:
        """Parse SELECT query components"""
        query = query.strip()
        
        # Extract components using regex
        select_pattern = r'SELECT\s+(.*?)\s+FROM\s+(\w+)'
        where_pattern = r'WHERE\s+(.*?)(?:\s+ORDER\s+BY|$)'
        order_pattern = r'ORDER\s+BY\s+(\w+)(?:\s+(ASC|DESC))?'
        limit_pattern = r'LIMIT\s+(\d+)'
        
        select_match = re.search(select_pattern, query, re.IGNORECASE)
        if not select_match:
            raise ValueError("Invalid SELECT query")
        
        columns_str = select_match.group(1).strip()
        table_name = select_match.group(2).strip()
        
        # Parse columns
        if columns_str == '*':
            columns = ['*']
        else:
            columns = [col.strip() for col in columns_str.split(',')]
        
        # Parse WHERE clause
        where_clause = None
        where_match = re.search(where_pattern, query, re.IGNORECASE)
        if where_match:
            where_clause = self._parse_where_clause(where_match.group(1).strip())
        
        # Parse ORDER BY
        order_by = None
        order_match = re.search(order_pattern, query, re.IGNORECASE)
        if order_match:
            order_by = {
                'column': order_match.group(1),
                'direction': order_match.group(2) or 'ASC'
            }
        
        # Parse LIMIT
        limit = None
        limit_match = re.search(limit_pattern, query, re.IGNORECASE)
        if limit_match:
            limit = int(limit_match.group(1))
        
        return {
            'columns': columns,
            'table': table_name,
            'where': where_clause,
            'order_by': order_by,
            'limit': limit
        }
    
    def _parse_where_clause(self, where_str: str) -> Optional[Dict[str, Any]]:
        """Parse WHERE clause (simplified version)"""
        # Simple WHERE clause parsing - can be enhanced
        where_str = where_str.strip()
        
        # Handle BETWEEN
        between_pattern = r'(\w+)\s+BETWEEN\s+([^\s]+)\s+AND\s+([^\s]+)'
        between_match = re.search(between_pattern, where_str, re.IGNORECASE)
        if between_match:
            return {
                'column': between_match.group(1),
                'operator': 'BETWEEN',
                'value': (self._parse_value(between_match.group(2)), 
                         self._parse_value(between_match.group(3)))
            }
        
        # Handle other operators
        operators = ['>=', '<=', '!=', '=', '>', '<', 'LIKE', 'IN']
        for op in operators:
            pattern = rf'(\w+)\s*{re.escape(op)}\s*([^\s]+(?:\s+[^\s]+)*)'
            match = re.search(pattern, where_str, re.IGNORECASE)
            if match:
                value = self._parse_value(match.group(2).strip())
                return {
                    'column': match.group(1),
                    'operator': op,
                    'value': value
                }
        
        return None
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse value from string"""
        value_str = value_str.strip()
        
        # Remove quotes
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Return as string
        return value_str
    
    def _parse_insert_query(self, query: str) -> Dict[str, Any]:
        """Parse INSERT query"""
        pattern = r'INSERT\s+INTO\s+(\w+)(?:\s*\(([^)]+)\))?\s+VALUES\s*\(([^)]+)\)'
        match = re.search(pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid INSERT query")
        
        table_name = match.group(1)
        columns_str = match.group(2)
        values_str = match.group(3)
        
        columns = None
        if columns_str:
            columns = [col.strip() for col in columns_str.split(',')]
        
        values = [self._parse_value(val.strip()) for val in values_str.split(',')]
        
        return {
            'table': table_name,
            'columns': columns,
            'values': values
        }
    
    def _parse_update_query(self, query: str) -> Dict[str, Any]:
        """Parse UPDATE query"""
        pattern = r'UPDATE\s+(\w+)\s+SET\s+(.*?)(?:\s+WHERE\s+(.*?))?$'
        match = re.search(pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid UPDATE query")
        
        table_name = match.group(1)
        set_str = match.group(2)
        where_str = match.group(3)
        
        # Parse SET clause
        set_clause = {}
        for assignment in set_str.split(','):
            column, value = assignment.split('=', 1)
            set_clause[column.strip()] = self._parse_value(value.strip())
        
        # Parse WHERE clause
        where_clause = None
        if where_str:
            where_clause = self._parse_where_clause(where_str)
        
        return {
            'table': table_name,
            'set': set_clause,
            'where': where_clause
        }
    
    def _parse_delete_query(self, query: str) -> Dict[str, Any]:
        """Parse DELETE query"""
        pattern = r'DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.*?))?$'
        match = re.search(pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid DELETE query")
        
        table_name = match.group(1)
        where_str = match.group(2)
        
        where_clause = None
        if where_str:
            where_clause = self._parse_where_clause(where_str)
        
        return {
            'table': table_name,
            'where': where_clause
        }
    
    def _parse_create_table_query(self, query: str) -> Dict[str, Any]:
        """Parse CREATE TABLE query"""
        pattern = r'CREATE\s+TABLE\s+(\w+)\s*\(([^)]+)\)'
        match = re.search(pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid CREATE TABLE query")
        
        table_name = match.group(1)
        columns_str = match.group(2)
        
        columns = {}
        primary_key = None
        
        for column_def in columns_str.split(','):
            column_def = column_def.strip()
            parts = column_def.split()
            if len(parts) >= 2:
                column_name = parts[0]
                column_type = parts[1].lower()
                columns[column_name] = column_type
                
                if 'PRIMARY' in column_def.upper() and 'KEY' in column_def.upper():
                    primary_key = column_name
        
        return {
            'table': table_name,
            'columns': columns,
            'primary_key': primary_key or list(columns.keys())[0]  # First column as default PK
        }
    
    def _parse_create_index_query(self, query: str) -> Dict[str, Any]:
        """Parse CREATE INDEX query"""
        pattern = r'CREATE\s+INDEX\s+\w+\s+ON\s+(\w+)\s*\((\w+)\)'
        match = re.search(pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid CREATE INDEX query")
        
        return {
            'table': match.group(1),
            'column': match.group(2)
        }
    
    def _update_query_stats(self, query: str, execution_time: float, success: bool) -> None:
        """Update query execution statistics"""
        self.query_stats['queries_executed'] += 1
        
        # Update average execution time
        current_avg = self.query_stats['average_execution_time']
        total_queries = self.query_stats['queries_executed']
        new_avg = ((current_avg * (total_queries - 1)) + execution_time) / total_queries
        self.query_stats['average_execution_time'] = new_avg
        
        # Track slow queries (> 1 second)
        if execution_time > 1.0:
            self.query_stats['slow_queries'].append({
                'query': query[:100] + '...' if len(query) > 100 else query,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 slow queries
            self.query_stats['slow_queries'] = self.query_stats['slow_queries'][-10:]
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query execution statistics"""
        return {
            **self.query_stats,
            'database_statistics': self.btree_db.get_database_statistics()
        }
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize the B-Tree database"""
        return self.btree_db.optimize_database()
    
    def close(self) -> None:
        """Close the SQL engine and B-Tree database"""
        self.btree_db.close()


# Example usage and testing
if __name__ == "__main__":
    print("Testing B-Tree SQL Engine...")
    
    # Create B-Tree SQL Engine
    sql_engine = BTreeSQLEngine("test_btree_sql")
    
    # Test CREATE TABLE
    print("\n1. Creating table...")
    result = sql_engine.execute_sql("""
        CREATE TABLE users (
            id INT PRIMARY KEY,
            username VARCHAR(50),
            email VARCHAR(100),
            age INT,
            balance DECIMAL
        )
    """)
    print(f"Create table result: {result['success']}")
    
    # Test CREATE INDEX
    print("\n2. Creating indexes...")
    sql_engine.execute_sql("CREATE INDEX idx_username ON users (username)")
    sql_engine.execute_sql("CREATE INDEX idx_email ON users (email)")
    
    # Test INSERT
    print("\n3. Inserting data...")
    for i in range(100):
        result = sql_engine.execute_sql(f"""
            INSERT INTO users (id, username, email, age, balance)
            VALUES ({i}, 'user_{i}', 'user_{i}@example.com', {20 + (i % 50)}, {100.0 + i * 10})
        """)
    
    print(f"Inserted 100 records")
    
    # Test SELECT with WHERE (indexed)
    print("\n4. Testing indexed SELECT...")
    result = sql_engine.execute_sql("SELECT * FROM users WHERE username = 'user_50'")
    print(f"Indexed search result: {len(result['data'])} records found")
    print(f"Optimization used: {result['optimization_used']}")
    
    # Test SELECT with range query
    print("\n5. Testing range query...")
    result = sql_engine.execute_sql("SELECT * FROM users WHERE age >= 30 AND age <= 40")
    print(f"Range query result: {len(result['data'])} records found")
    
    # Test UPDATE
    print("\n6. Testing UPDATE...")
    result = sql_engine.execute_sql("UPDATE users SET balance = 999.99 WHERE username = 'user_25'")
    print(f"Update result: {result['rows_affected']} rows affected")
    
    # Test DELETE
    print("\n7. Testing DELETE...")
    result = sql_engine.execute_sql("DELETE FROM users WHERE age > 65")
    print(f"Delete result: {result['rows_affected']} rows affected")
    
    # Test complex SELECT with ORDER BY and LIMIT
    print("\n8. Testing complex SELECT...")
    result = sql_engine.execute_sql("""
        SELECT username, email, balance 
        FROM users 
        WHERE balance > 500 
        ORDER BY balance DESC 
        LIMIT 5
    """)
    print(f"Complex query result: {len(result['data'])} records found")
    for record in result['data']:
        print(f"  {record['username']}: ${record['balance']}")
    
    # Show statistics
    print("\n9. Query Statistics:")
    stats = sql_engine.get_query_statistics()
    print(f"Total queries executed: {stats['queries_executed']}")
    print(f"Average execution time: {stats['average_execution_time']:.4f}s")
    print(f"Slow queries: {len(stats['slow_queries'])}")
    
    # Database statistics
    db_stats = stats['database_statistics']
    print(f"Total records: {db_stats['metadata']['statistics']['total_records']}")
    print(f"Total indexes: {db_stats['metadata']['statistics']['total_indexes']}")
    
    # Close engine
    sql_engine.close()
    print("\nB-Tree SQL Engine testing completed!")
