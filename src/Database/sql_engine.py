"""
SQL Query Engine for Blockchain Database
=======================================

A comprehensive SQL parser and executor that translates SQL queries to MongoDB-style operations.
Supports SELECT, INSERT, UPDATE, DELETE, JOINs, ORDER BY, GROUP BY, subqueries, and more.
"""

import re
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date
import uuid


class SQLTokenType(Enum):
    """SQL token types for parsing"""
    KEYWORD = "keyword"
    IDENTIFIER = "identifier"
    STRING = "string"
    NUMBER = "number"
    OPERATOR = "operator"
    PUNCTUATION = "punctuation"
    WHITESPACE = "whitespace"
    EOF = "eof"


class JoinType(Enum):
    """SQL JOIN types"""
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"
    CROSS = "CROSS"


class OperationType(Enum):
    """SQL operation types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"


@dataclass
class SQLToken:
    """Represents a SQL token"""
    type: SQLTokenType
    value: str
    position: int


@dataclass
class Column:
    """Represents a column in SQL query"""
    name: str
    table: Optional[str] = None
    alias: Optional[str] = None
    function: Optional[str] = None  # For aggregation functions
    
    def __str__(self):
        if self.table:
            return f"{self.table}.{self.name}"
        return self.name


@dataclass
class Table:
    """Represents a table/collection in SQL query"""
    name: str
    alias: Optional[str] = None
    
    def get_name(self) -> str:
        return self.alias if self.alias else self.name


@dataclass
class JoinClause:
    """Represents a JOIN clause"""
    type: JoinType
    table: Table
    condition: Dict[str, Any]  # MongoDB-style condition


@dataclass
class WhereCondition:
    """Represents a WHERE condition"""
    field: str
    operator: str
    value: Any
    logical_operator: Optional[str] = None  # AND, OR, NOT


@dataclass
class OrderByClause:
    """Represents an ORDER BY clause"""
    column: Column
    direction: str = "ASC"  # ASC or DESC


@dataclass
class GroupByClause:
    """Represents a GROUP BY clause"""
    columns: List[Column]
    having: Optional[List[WhereCondition]] = None


@dataclass
class SQLQuery:
    """Represents a parsed SQL query"""
    operation: OperationType
    tables: List[Table] = field(default_factory=list)
    columns: List[Column] = field(default_factory=list)
    joins: List[JoinClause] = field(default_factory=list)
    where_conditions: List[WhereCondition] = field(default_factory=list)
    group_by: Optional[GroupByClause] = None
    order_by: List[OrderByClause] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    values: Dict[str, Any] = field(default_factory=dict)  # For INSERT/UPDATE
    set_values: Dict[str, Any] = field(default_factory=dict)  # For UPDATE


class SQLLexer:
    """SQL lexer for tokenizing SQL statements"""
    
    KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS',
        'ON', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CREATE', 'TABLE',
        'DROP', 'ALTER', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'AS',
        'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'TRUE', 'FALSE',
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DISTINCT', 'ASC', 'DESC'
    }
    
    OPERATORS = {
        '=', '!=', '<>', '<', '>', '<=', '>=', '+', '-', '*', '/', '%', '||'
    }
    
    def __init__(self, sql: str):
        self.sql = sql.strip()
        self.position = 0
        self.tokens: List[SQLToken] = []
    
    def tokenize(self) -> List[SQLToken]:
        """Tokenize the SQL string"""
        while self.position < len(self.sql):
            self._skip_whitespace()
            
            if self.position >= len(self.sql):
                break
            
            char = self.sql[self.position]
            
            if char == "'":
                self._tokenize_string()
            elif char == '"':
                self._tokenize_quoted_identifier()
            elif char.isdigit() or (char == '.' and self.position + 1 < len(self.sql) and self.sql[self.position + 1].isdigit()):
                self._tokenize_number()
            elif char.isalpha() or char == '_':
                self._tokenize_identifier_or_keyword()
            elif char in '(),;':
                self.tokens.append(SQLToken(SQLTokenType.PUNCTUATION, char, self.position))
                self.position += 1
            else:
                self._tokenize_operator()
        
        self.tokens.append(SQLToken(SQLTokenType.EOF, '', self.position))
        return self.tokens
    
    def _skip_whitespace(self):
        """Skip whitespace characters"""
        while self.position < len(self.sql) and self.sql[self.position].isspace():
            self.position += 1
    
    def _tokenize_string(self):
        """Tokenize string literals"""
        start_pos = self.position
        self.position += 1  # Skip opening quote
        value = ""
        
        while self.position < len(self.sql):
            char = self.sql[self.position]
            if char == "'":
                if self.position + 1 < len(self.sql) and self.sql[self.position + 1] == "'":
                    # Escaped quote
                    value += "'"
                    self.position += 2
                else:
                    # End of string
                    self.position += 1
                    break
            else:
                value += char
                self.position += 1
        
        self.tokens.append(SQLToken(SQLTokenType.STRING, value, start_pos))
    
    def _tokenize_quoted_identifier(self):
        """Tokenize quoted identifiers"""
        start_pos = self.position
        self.position += 1  # Skip opening quote
        value = ""
        
        while self.position < len(self.sql) and self.sql[self.position] != '"':
            value += self.sql[self.position]
            self.position += 1
        
        if self.position < len(self.sql):
            self.position += 1  # Skip closing quote
        
        self.tokens.append(SQLToken(SQLTokenType.IDENTIFIER, value, start_pos))
    
    def _tokenize_number(self):
        """Tokenize numeric literals"""
        start_pos = self.position
        value = ""
        has_dot = False
        
        while self.position < len(self.sql):
            char = self.sql[self.position]
            if char.isdigit():
                value += char
                self.position += 1
            elif char == '.' and not has_dot:
                has_dot = True
                value += char
                self.position += 1
            else:
                break
        
        self.tokens.append(SQLToken(SQLTokenType.NUMBER, value, start_pos))
    
    def _tokenize_identifier_or_keyword(self):
        """Tokenize identifiers and keywords"""
        start_pos = self.position
        value = ""
        
        while self.position < len(self.sql):
            char = self.sql[self.position]
            if char.isalnum() or char == '_':
                value += char
                self.position += 1
            else:
                break
        
        token_type = SQLTokenType.KEYWORD if value.upper() in self.KEYWORDS else SQLTokenType.IDENTIFIER
        self.tokens.append(SQLToken(token_type, value.upper() if token_type == SQLTokenType.KEYWORD else value, start_pos))
    
    def _tokenize_operator(self):
        """Tokenize operators"""
        start_pos = self.position
        
        # Check for two-character operators first
        if self.position + 1 < len(self.sql):
            two_char = self.sql[self.position:self.position + 2]
            if two_char in self.OPERATORS:
                self.tokens.append(SQLToken(SQLTokenType.OPERATOR, two_char, start_pos))
                self.position += 2
                return
        
        # Single character operator
        char = self.sql[self.position]
        if char in self.OPERATORS:
            self.tokens.append(SQLToken(SQLTokenType.OPERATOR, char, start_pos))
        else:
            # Unknown character, treat as punctuation
            self.tokens.append(SQLToken(SQLTokenType.PUNCTUATION, char, start_pos))
        
        self.position += 1


class SQLParser:
    """SQL parser for building AST from tokens"""
    
    def __init__(self, tokens: List[SQLToken]):
        self.tokens = tokens
        self.position = 0
        self.current_token = tokens[0] if tokens else None
    
    def parse(self) -> SQLQuery:
        """Parse tokens into SQLQuery object"""
        if not self.current_token:
            raise ValueError("Empty SQL query")
        
        if self.current_token.value == "SELECT":
            return self._parse_select()
        elif self.current_token.value == "INSERT":
            return self._parse_insert()
        elif self.current_token.value == "UPDATE":
            return self._parse_update()
        elif self.current_token.value == "DELETE":
            return self._parse_delete()
        elif self.current_token.value == "CREATE":
            return self._parse_create()
        elif self.current_token.value == "DROP":
            return self._parse_drop()
        else:
            raise ValueError(f"Unsupported SQL operation: {self.current_token.value}")
    
    def _advance(self):
        """Move to next token"""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None
    
    def _current_token_value(self) -> str:
        """Get current token value safely"""
        if not self.current_token:
            raise ValueError("Unexpected end of tokens")
        return self.current_token.value
    
    def _current_token_type(self):
        """Get current token type safely"""
        if not self.current_token:
            raise ValueError("Unexpected end of tokens")
        return self.current_token.type
    
    def _expect(self, expected_value: str):
        """Expect a specific token value"""
        if not self.current_token or self.current_token.value != expected_value:
            raise ValueError(f"Expected '{expected_value}', got '{self.current_token.value if self.current_token else 'EOF'}'")
        self._advance()
    
    def _parse_select(self) -> SQLQuery:
        """Parse SELECT statement"""
        query = SQLQuery(operation=OperationType.SELECT)
        self._advance()  # Skip SELECT
        
        # Parse columns
        query.columns = self._parse_column_list()
        
        # Parse FROM clause
        if self.current_token and self.current_token.value == "FROM":
            self._advance()
            query.tables = self._parse_table_list()
        
        # Parse JOINs
        while self.current_token and self.current_token.value in ["JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS"]:
            query.joins.append(self._parse_join())
        
        # Parse WHERE clause
        if self.current_token and self.current_token.value == "WHERE":
            self._advance()
            query.where_conditions = self._parse_where_conditions()
        
        # Parse GROUP BY
        if self.current_token and self.current_token.value == "GROUP":
            query.group_by = self._parse_group_by()
        
        # Parse ORDER BY
        if self.current_token and self.current_token.value == "ORDER":
            query.order_by = self._parse_order_by()
        
        # Parse LIMIT
        if self.current_token and self.current_token.value == "LIMIT":
            query.limit = self._parse_limit()
        
        # Parse OFFSET
        if self.current_token and self.current_token.value == "OFFSET":
            query.offset = self._parse_offset()
        
        return query
    
    def _parse_column_list(self) -> List[Column]:
        """Parse column list in SELECT"""
        columns = []
        
        while True:
            if self.current_token and self.current_token.value == "*":
                columns.append(Column(name="*"))
                self._advance()
            elif self.current_token and self.current_token.type == SQLTokenType.IDENTIFIER:
                column = self._parse_column()
                columns.append(column)
            elif self.current_token and self.current_token.value in ["COUNT", "SUM", "AVG", "MIN", "MAX"]:
                column = self._parse_aggregate_function()
                columns.append(column)
            else:
                break
            
            if self.current_token and self.current_token.value == ",":
                self._advance()
            else:
                break
        
        return columns
    
    def _parse_column(self) -> Column:
        """Parse a single column"""
        if not self.current_token:
            raise ValueError("Unexpected end of tokens")
            
        table = None
        name = self.current_token.value
        self._advance()
        
        # Check for table.column syntax
        if self.current_token and self.current_token.value == ".":
            self._advance()
            table = name
            if not self.current_token:
                raise ValueError("Expected column name after '.'")
            name = self.current_token.value
            self._advance()
        
        # Check for alias
        alias = None
        if self.current_token and self.current_token.value == "AS":
            self._advance()
            alias = self.current_token.value
            self._advance()
        elif self.current_token and self.current_token.type == SQLTokenType.IDENTIFIER:
            # Implicit alias
            alias = self.current_token.value
            self._advance()
        
        return Column(name=name, table=table, alias=alias)
    
    def _parse_aggregate_function(self) -> Column:
        """Parse aggregate function"""
        function = self._current_token_value()
        self._advance()
        
        self._expect("(")
        
        if self.current_token and self._current_token_value() == "*":
            name = "*"
            self._advance()
        else:
            column = self._parse_column()
            name = str(column)
        
        self._expect(")")
        
        # Check for alias
        alias = None
        if self.current_token and self.current_token.value == "AS":
            self._advance()
            alias = self.current_token.value
            self._advance()
        
        return Column(name=name, function=function, alias=alias)
    
    def _parse_table_list(self) -> List[Table]:
        """Parse table list in FROM clause"""
        tables = []
        
        while True:
            if self.current_token and self.current_token.type == SQLTokenType.IDENTIFIER:
                name = self.current_token.value
                self._advance()
                
                # Check for alias
                alias = None
                if self.current_token and self.current_token.value == "AS":
                    self._advance()
                    alias = self.current_token.value
                    self._advance()
                elif self.current_token and self.current_token.type == SQLTokenType.IDENTIFIER:
                    # Implicit alias
                    alias = self.current_token.value
                    self._advance()
                
                tables.append(Table(name=name, alias=alias))
            else:
                break
            
            if self.current_token and self.current_token.value == ",":
                self._advance()
            else:
                break
        
        return tables
    
    def _parse_join(self) -> JoinClause:
        """Parse JOIN clause"""
        join_type = JoinType.INNER  # Default
        
        if self.current_token and self._current_token_value() in ["LEFT", "RIGHT", "FULL", "CROSS"]:
            join_type = JoinType(self._current_token_value())
            self._advance()
        
        if self.current_token and self.current_token.value == "JOIN":
            self._advance()
        
        # Parse table
        table_name = self._current_token_value()
        self._advance()
        
        alias = None
        if self.current_token and self.current_token.value == "AS":
            self._advance()
            alias = self.current_token.value
            self._advance()
        elif self.current_token and self.current_token.type == SQLTokenType.IDENTIFIER:
            alias = self.current_token.value
            self._advance()
        
        table = Table(name=table_name, alias=alias)
        
        # Parse ON condition
        condition = {}
        if self.current_token and self.current_token.value == "ON":
            self._advance()
            condition = self._parse_join_condition()
        
        return JoinClause(type=join_type, table=table, condition=condition)
    
    def _parse_join_condition(self) -> Dict[str, Any]:
        """Parse JOIN ON condition"""
        # Simplified join condition parsing
        left_column = self._current_token_value()
        self._advance()
        
        if self.current_token and self.current_token.value == ".":
            self._advance()
            left_column += "." + self._current_token_value()
            self._advance()
        
        operator = self._current_token_value()
        self._advance()
        
        right_column = self._current_token_value()
        self._advance()
        
        if self.current_token and self.current_token.value == ".":
            self._advance()
            right_column += "." + self.current_token.value
            self._advance()
        
        return {
            "left": left_column,
            "operator": operator,
            "right": right_column
        }
    
    def _parse_where_conditions(self) -> List[WhereCondition]:
        """Parse WHERE conditions"""
        conditions = []
        
        while self.current_token and self.current_token.value not in ["GROUP", "ORDER", "LIMIT", "OFFSET"]:
            condition = self._parse_single_condition()
            conditions.append(condition)
            
            if self.current_token and self.current_token.value in ["AND", "OR"]:
                condition.logical_operator = self.current_token.value
                self._advance()
            else:
                break
        
        return conditions
    
    def _parse_single_condition(self) -> WhereCondition:
        """Parse a single WHERE condition"""
        field = self._current_token_value()
        self._advance()
        
        if self.current_token and self.current_token.value == ".":
            self._advance()
            field += "." + self._current_token_value()
            self._advance()
        
        operator = self._current_token_value()
        self._advance()
        
        if self._current_token_type() == SQLTokenType.STRING:
            value = self._current_token_value()
        elif self._current_token_type() == SQLTokenType.NUMBER:
            token_value = self._current_token_value()
            value = float(token_value) if '.' in token_value else int(token_value)
        else:
            value = self._current_token_value()
        
        self._advance()
        
        return WhereCondition(field=field, operator=operator, value=value)
    
    def _parse_group_by(self) -> GroupByClause:
        """Parse GROUP BY clause"""
        self._expect("GROUP")
        self._expect("BY")
        
        columns = []
        while True:
            column = self._parse_column()
            columns.append(column)
            
            if self.current_token and self.current_token.value == ",":
                self._advance()
            else:
                break
        
        having = None
        if self.current_token and self.current_token.value == "HAVING":
            self._advance()
            having = self._parse_where_conditions()
        
        return GroupByClause(columns=columns, having=having)
    
    def _parse_order_by(self) -> List[OrderByClause]:
        """Parse ORDER BY clause"""
        self._expect("ORDER")
        self._expect("BY")
        
        order_clauses = []
        while True:
            column = self._parse_column()
            direction = "ASC"
            
            if self.current_token and self.current_token.value in ["ASC", "DESC"]:
                direction = self.current_token.value
                self._advance()
            
            order_clauses.append(OrderByClause(column=column, direction=direction))
            
            if self.current_token and self.current_token.value == ",":
                self._advance()
            else:
                break
        
        return order_clauses
    
    def _parse_limit(self) -> int:
        """Parse LIMIT clause"""
        self._expect("LIMIT")
        limit = int(self._current_token_value())
        self._advance()
        return limit
    
    def _parse_offset(self) -> int:
        """Parse OFFSET clause"""
        self._expect("OFFSET")
        offset = int(self._current_token_value())
        self._advance()
        return offset
    
    def _parse_insert(self) -> SQLQuery:
        """Parse INSERT statement"""
        query = SQLQuery(operation=OperationType.INSERT)
        self._advance()  # Skip INSERT
        
        self._expect("INTO")
        table_name = self._current_token_value()
        query.tables.append(Table(name=table_name))
        self._advance()
        
        # Parse column list
        if self.current_token and self.current_token.value == "(":
            self._advance()
            columns = []
            while self.current_token and self.current_token.value != ")":
                columns.append(Column(name=self._current_token_value()))
                self._advance()
                if self.current_token and self.current_token.value == ",":
                    self._advance()
            self._expect(")")
            query.columns = columns
        
        # Parse VALUES
        self._expect("VALUES")
        self._expect("(")
        
        values = {}
        value_index = 0
        while self.current_token and self.current_token.value != ")":
            if self.current_token.type == SQLTokenType.STRING:
                value = self.current_token.value
            elif self.current_token.type == SQLTokenType.NUMBER:
                value = float(self.current_token.value) if '.' in self.current_token.value else int(self.current_token.value)
            else:
                value = self.current_token.value
            
            if query.columns and value_index < len(query.columns):
                values[query.columns[value_index].name] = value
            else:
                values[f"field_{value_index}"] = value
            
            value_index += 1
            self._advance()
            
            if self.current_token and self.current_token.value == ",":
                self._advance()
        
        self._expect(")")
        query.values = values
        
        return query
    
    def _parse_update(self) -> SQLQuery:
        """Parse UPDATE statement"""
        query = SQLQuery(operation=OperationType.UPDATE)
        self._advance()  # Skip UPDATE
        
        table_name = self._current_token_value()
        query.tables.append(Table(name=table_name))
        self._advance()
        
        self._expect("SET")
        
        # Parse SET clauses
        set_values = {}
        while True:
            field = self._current_token_value()
            self._advance()
            self._expect("=")
            
            if self._current_token_type() == SQLTokenType.STRING:
                value = self._current_token_value()
            elif self._current_token_type() == SQLTokenType.NUMBER:
                token_value = self._current_token_value()
                value = float(token_value) if '.' in token_value else int(token_value)
            else:
                value = self._current_token_value()
            
            set_values[field] = value
            self._advance()
            
            if self.current_token and self.current_token.value == ",":
                self._advance()
            else:
                break
        
        query.set_values = set_values
        
        # Parse WHERE clause
        if self.current_token and self.current_token.value == "WHERE":
            self._advance()
            query.where_conditions = self._parse_where_conditions()
        
        return query
    
    def _parse_delete(self) -> SQLQuery:
        """Parse DELETE statement"""
        query = SQLQuery(operation=OperationType.DELETE)
        self._advance()  # Skip DELETE
        
        self._expect("FROM")
        table_name = self._current_token_value()
        query.tables.append(Table(name=table_name))
        self._advance()
        
        # Parse WHERE clause
        if self.current_token and self.current_token.value == "WHERE":
            self._advance()
            query.where_conditions = self._parse_where_conditions()
        
        return query
    
    def _parse_create(self) -> SQLQuery:
        """Parse CREATE statement"""
        query = SQLQuery(operation=OperationType.CREATE)
        self._advance()  # Skip CREATE
        
        self._expect("TABLE")
        table_name = self._current_token_value()
        query.tables.append(Table(name=table_name))
        self._advance()
        
        # Parse column definitions (simplified)
        if self.current_token and self.current_token.value == "(":
            self._advance()
            columns = []
            while self.current_token and self.current_token.value != ")":
                column_name = self.current_token.value
                columns.append(Column(name=column_name))
                self._advance()
                
                # Skip column type and constraints for now
                while self.current_token and self.current_token.value not in [",", ")"]:
                    self._advance()
                
                if self.current_token and self.current_token.value == ",":
                    self._advance()
            
            self._expect(")")
            query.columns = columns
        
        return query
    
    def _parse_drop(self) -> SQLQuery:
        """Parse DROP statement"""
        query = SQLQuery(operation=OperationType.DROP)
        self._advance()  # Skip DROP
        
        self._expect("TABLE")
        table_name = self._current_token_value()
        query.tables.append(Table(name=table_name))
        self._advance()
        
        return query


class SQLExecutor:
    """Execute SQL queries against the MongoDB-style database"""
    
    def __init__(self, db_engine):
        self.db_engine = db_engine
    
    def execute(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            # Tokenize and parse SQL
            lexer = SQLLexer(sql)
            tokens = lexer.tokenize()
            
            parser = SQLParser(tokens)
            query = parser.parse()
            
            # Execute based on operation type
            if query.operation == OperationType.SELECT:
                return self._execute_select(query)
            elif query.operation == OperationType.INSERT:
                return self._execute_insert(query)
            elif query.operation == OperationType.UPDATE:
                return self._execute_update(query)
            elif query.operation == OperationType.DELETE:
                return self._execute_delete(query)
            elif query.operation == OperationType.CREATE:
                return self._execute_create(query)
            elif query.operation == OperationType.DROP:
                return self._execute_drop(query)
            else:
                return {"success": False, "error": f"Unsupported operation: {query.operation}"}
        
        except Exception as e:
            return {"success": False, "error": f"SQL execution error: {str(e)}"}
    
    def _execute_select(self, query: SQLQuery) -> Dict[str, Any]:
        """Execute SELECT query"""
        if not query.tables:
            return {"success": False, "error": "No table specified in FROM clause"}
        
        main_table = query.tables[0]
        collection_name = main_table.name
        
        # Build MongoDB filter from WHERE conditions
        filter_dict = self._build_filter(query.where_conditions)
        
        # Handle JOINs
        if query.joins:
            return self._execute_select_with_joins(query, filter_dict)
        
        # Execute basic find
        result = self.db_engine.find(
            collection_name,
            filter_dict,
            self._build_projection(query.columns),
            self._build_sort(query.order_by),
            query.limit,
            query.offset or 0
        )
        
        if not result.get("success", True):
            return result
        
        documents = result.get("documents", [])
        
        # Handle GROUP BY
        if query.group_by:
            documents = self._apply_group_by(documents, query.group_by)
        
        # Handle aggregation functions
        if any(col.function for col in query.columns):
            documents = self._apply_aggregation(documents, query.columns)
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents)
        }
    
    def _execute_select_with_joins(self, query: SQLQuery, base_filter: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SELECT with JOINs"""
        main_table = query.tables[0]
        
        # Get documents from main table
        main_result = self.db_engine.find(main_table.name, base_filter)
        if not main_result.get("success", True):
            return main_result
        
        main_documents = main_result.get("documents", [])
        
        # Apply JOINs
        for join in query.joins:
            main_documents = self._apply_join(main_documents, join, main_table)
        
        # Apply projection, sorting, etc.
        if query.order_by:
            main_documents = self._apply_sort_to_documents(main_documents, query.order_by)
        
        if query.limit:
            main_documents = main_documents[:query.limit]
        
        return {
            "success": True,
            "documents": main_documents,
            "count": len(main_documents)
        }
    
    def _apply_join(self, left_documents: List[Dict[str, Any]], join: JoinClause, main_table: Table) -> List[Dict[str, Any]]:
        """Apply JOIN operation"""
        # Get right table documents
        right_result = self.db_engine.find(join.table.name)
        if not right_result.get("success", True):
            return left_documents
        
        right_documents = right_result.get("documents", [])
        
        # Extract join condition
        left_field = join.condition.get("left", "").replace(f"{main_table.get_name()}.", "")
        right_field = join.condition.get("right", "").replace(f"{join.table.get_name()}.", "")
        
        joined_documents = []
        
        for left_doc in left_documents:
            matches = []
            
            for right_doc in right_documents:
                if self._join_condition_matches(left_doc, right_doc, left_field, right_field, join.condition.get("operator", "=")):
                    # Create joined document
                    joined_doc = left_doc.copy()
                    
                    # Add right table fields with table prefix
                    table_prefix = join.table.get_name()
                    for key, value in right_doc.items():
                        if key != "_id":  # Don't duplicate IDs
                            joined_doc[f"{table_prefix}.{key}"] = value
                    
                    matches.append(joined_doc)
            
            if join.type == JoinType.INNER:
                joined_documents.extend(matches)
            elif join.type == JoinType.LEFT:
                if matches:
                    joined_documents.extend(matches)
                else:
                    # Add left document with null values for right table
                    null_doc = left_doc.copy()
                    table_prefix = join.table.get_name()
                    # Add null fields from right table (simplified)
                    joined_documents.append(null_doc)
            # Add other JOIN types as needed
        
        return joined_documents
    
    def _join_condition_matches(self, left_doc: Dict[str, Any], right_doc: Dict[str, Any], 
                               left_field: str, right_field: str, operator: str) -> bool:
        """Check if join condition matches"""
        left_value = self._get_nested_value(left_doc, left_field)
        right_value = self._get_nested_value(right_doc, right_field)
        
        if operator == "=":
            return left_value == right_value
        elif operator == "!=":
            return left_value != right_value
        elif operator == "<":
            return left_value < right_value
        elif operator == "<=":
            return left_value <= right_value
        elif operator == ">":
            return left_value > right_value
        elif operator == ">=":
            return left_value >= right_value
        
        return False
    
    def _build_filter(self, conditions: List[WhereCondition]) -> Dict[str, Any]:
        """Build MongoDB filter from WHERE conditions"""
        if not conditions:
            return {}
        
        filter_dict = {}
        current_group = []
        
        for condition in conditions:
            mongo_condition = self._condition_to_mongo(condition)
            current_group.append(mongo_condition)
            
            # Handle logical operators
            if condition.logical_operator == "OR":
                if len(current_group) > 1:
                    filter_dict.setdefault("$or", []).extend(current_group)
                    current_group = []
                else:
                    filter_dict.setdefault("$or", []).append(current_group[0])
                    current_group = []
            elif condition.logical_operator == "AND" or not condition.logical_operator:
                # Continue building current group
                pass
        
        # Add remaining conditions
        if current_group:
            if len(current_group) == 1:
                filter_dict.update(current_group[0])
            else:
                filter_dict.setdefault("$and", []).extend(current_group)
        
        return filter_dict
    
    def _condition_to_mongo(self, condition: WhereCondition) -> Dict[str, Any]:
        """Convert SQL condition to MongoDB filter"""
        field = condition.field
        operator = condition.operator
        value = condition.value
        
        if operator == "=":
            return {field: value}
        elif operator in ["!=", "<>"]:
            return {field: {"$ne": value}}
        elif operator == "<":
            return {field: {"$lt": value}}
        elif operator == "<=":
            return {field: {"$lte": value}}
        elif operator == ">":
            return {field: {"$gt": value}}
        elif operator == ">=":
            return {field: {"$gte": value}}
        elif operator == "LIKE":
            # Convert SQL LIKE to MongoDB regex
            regex_pattern = value.replace("%", ".*").replace("_", ".")
            return {field: {"$regex": regex_pattern, "$options": "i"}}
        elif operator == "IN":
            return {field: {"$in": value if isinstance(value, list) else [value]}}
        elif operator == "NOT IN":
            return {field: {"$nin": value if isinstance(value, list) else [value]}}
        else:
            return {field: value}
    
    def _build_projection(self, columns: List[Column]) -> Optional[Dict[str, int]]:
        """Build MongoDB projection from SELECT columns"""
        if not columns or any(col.name == "*" for col in columns):
            return None
        
        projection = {}
        for column in columns:
            if column.function:
                # Aggregation functions are handled separately
                continue
            projection[column.name] = 1
        
        return projection if projection else None
    
    def _build_sort(self, order_clauses: List[OrderByClause]) -> Optional[Dict[str, int]]:
        """Build MongoDB sort from ORDER BY"""
        if not order_clauses:
            return None
        
        sort_dict = {}
        for clause in order_clauses:
            direction = 1 if clause.direction == "ASC" else -1
            sort_dict[clause.column.name] = direction
        
        return sort_dict
    
    def _apply_group_by(self, documents: List[Dict[str, Any]], group_by: GroupByClause) -> List[Dict[str, Any]]:
        """Apply GROUP BY to documents"""
        groups = {}
        
        for doc in documents:
            # Build group key
            group_key_parts = []
            for column in group_by.columns:
                value = self._get_nested_value(doc, column.name)
                group_key_parts.append(str(value))
            
            group_key = "|".join(group_key_parts)
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(doc)
        
        # Create grouped results
        grouped_documents = []
        for group_key, group_docs in groups.items():
            group_result = {}
            
            # Add grouping fields
            key_parts = group_key.split("|")
            for i, column in enumerate(group_by.columns):
                if i < len(key_parts):
                    group_result[column.name] = key_parts[i]
            
            # Add first document's other fields (simplified)
            if group_docs:
                for key, value in group_docs[0].items():
                    if key not in group_result:
                        group_result[key] = value
            
            grouped_documents.append(group_result)
        
        return grouped_documents
    
    def _apply_aggregation(self, documents: List[Dict[str, Any]], columns: List[Column]) -> List[Dict[str, Any]]:
        """Apply aggregation functions"""
        if not documents:
            return []
        
        result = {}
        
        for column in columns:
            if column.function:
                field_name = column.alias or f"{column.function.lower()}_{column.name}"
                
                if column.function == "COUNT":
                    if column.name == "*":
                        result[field_name] = len(documents)
                    else:
                        count = sum(1 for doc in documents if column.name in doc and doc[column.name] is not None)
                        result[field_name] = count
                
                elif column.function in ["SUM", "AVG"]:
                    values = [self._get_nested_value(doc, column.name) for doc in documents]
                    numeric_values = [v for v in values if isinstance(v, (int, float))]
                    
                    if column.function == "SUM":
                        result[field_name] = sum(numeric_values)
                    else:  # AVG
                        result[field_name] = sum(numeric_values) / len(numeric_values) if numeric_values else 0
                
                elif column.function == "MIN":
                    values = [self._get_nested_value(doc, column.name) for doc in documents]
                    result[field_name] = min(v for v in values if v is not None) if values else None
                
                elif column.function == "MAX":
                    values = [self._get_nested_value(doc, column.name) for doc in documents]
                    result[field_name] = max(v for v in values if v is not None) if values else None
            
            elif column.name != "*":
                # Regular column
                if documents:
                    result[column.name] = self._get_nested_value(documents[0], column.name)
        
        return [result]
    
    def _apply_sort_to_documents(self, documents: List[Dict[str, Any]], order_clauses: List[OrderByClause]) -> List[Dict[str, Any]]:
        """Apply sorting to document list"""
        def sort_key(doc):
            key_parts = []
            for clause in order_clauses:
                value = self._get_nested_value(doc, clause.column.name)
                if clause.direction == "DESC":
                    # For descending, we need to reverse the comparison
                    if isinstance(value, (int, float)):
                        value = -value
                    elif isinstance(value, str):
                        # For strings, we'll handle this in the comparison
                        pass
                key_parts.append((value, clause.direction))
            return key_parts
        
        return sorted(documents, key=sort_key)
    
    def _execute_insert(self, query: SQLQuery) -> Dict[str, Any]:
        """Execute INSERT query"""
        if not query.tables:
            return {"success": False, "error": "No table specified"}
        
        collection_name = query.tables[0].name
        
        # Add timestamp and ID if not present
        document = query.values.copy()
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        if "created_at" not in document:
            document["created_at"] = datetime.now()
        
        return self.db_engine.insert_one(collection_name, document)
    
    def _execute_update(self, query: SQLQuery) -> Dict[str, Any]:
        """Execute UPDATE query"""
        if not query.tables:
            return {"success": False, "error": "No table specified"}
        
        collection_name = query.tables[0].name
        filter_dict = self._build_filter(query.where_conditions)
        
        # Build update operation
        update_dict = {"$set": query.set_values}
        if "updated_at" not in query.set_values:
            update_dict["$set"]["updated_at"] = datetime.now()
        
        return self.db_engine.update_many(collection_name, filter_dict, update_dict)
    
    def _execute_delete(self, query: SQLQuery) -> Dict[str, Any]:
        """Execute DELETE query (moves to archive)"""
        if not query.tables:
            return {"success": False, "error": "No table specified"}
        
        collection_name = query.tables[0].name
        filter_dict = self._build_filter(query.where_conditions)
        
        # Instead of deleting, move to archive
        return self._archive_documents(collection_name, filter_dict)
    
    def _archive_documents(self, collection_name: str, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Archive documents instead of deleting them"""
        # Find documents to archive
        result = self.db_engine.find(collection_name, filter_dict)
        if not result.get("success", True):
            return result
        
        documents = result.get("documents", [])
        if not documents:
            return {"success": True, "archived_count": 0}
        
        # Create archive collection name
        archive_collection = f"{collection_name}_archive"
        
        # Ensure archive collection exists
        self.db_engine.create_collection(archive_collection)
        
        # Add archive metadata to documents
        archived_documents = []
        for doc in documents:
            archived_doc = doc.copy()
            archived_doc["archived_at"] = datetime.now()
            archived_doc["archived_from"] = collection_name
            archived_doc["archive_reason"] = "SQL DELETE operation"
            archived_documents.append(archived_doc)
        
        # Insert into archive
        archive_result = self.db_engine.insert_many(archive_collection, archived_documents)
        if not archive_result.get("success", True):
            return archive_result
        
        # Remove from original collection
        delete_result = self.db_engine.delete_many(collection_name, filter_dict)
        
        return {
            "success": True,
            "archived_count": len(documents),
            "deleted_count": delete_result.get("deleted_count", 0)
        }
    
    def _execute_create(self, query: SQLQuery) -> Dict[str, Any]:
        """Execute CREATE TABLE query"""
        if not query.tables:
            return {"success": False, "error": "No table name specified"}
        
        collection_name = query.tables[0].name
        
        # Build schema from columns
        schema = {}
        for column in query.columns:
            schema[column.name] = {
                "type": "string",  # Default type
                "required": False
            }
        
        return self.db_engine.create_collection(collection_name, schema)
    
    def _execute_drop(self, query: SQLQuery) -> Dict[str, Any]:
        """Execute DROP TABLE query"""
        if not query.tables:
            return {"success": False, "error": "No table name specified"}
        
        collection_name = query.tables[0].name
        return self.db_engine.drop_collection(collection_name)
    
    def _get_nested_value(self, document: Dict[str, Any], field: str) -> Any:
        """Get nested field value from document"""
        keys = field.split(".")
        value = document
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


class SQLEngine:
    """Main SQL Engine interface for the blockchain database"""
    
    def __init__(self, db_engine):
        """Initialize SQL engine with database engine"""
        self.db_engine = db_engine
        self.executor = SQLExecutor(db_engine)
    
    def execute_query(self, sql_query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a SQL query and return results"""
        try:
            # Create lexer and parser for this query
            lexer = SQLLexer(sql_query)
            tokens = lexer.tokenize()
            
            parser = SQLParser(tokens)
            query = parser.parse()
            
            # Apply parameters if provided
            if parameters:
                sql_query = self._apply_parameters(sql_query, parameters)
            
            # Execute the query using the executor
            result = self.executor.execute(sql_query)
            
            return result
            
        except Exception as e:
            raise Exception(f"SQL execution error: {str(e)}")
    
    def explain_query(self, sql_query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Explain a SQL query without executing it"""
        try:
            # Apply parameters if provided
            if parameters:
                sql_query = self._apply_parameters(sql_query, parameters)
            
            # Tokenize and parse
            lexer = SQLLexer(sql_query)
            tokens = lexer.tokenize()
            parser = SQLParser(tokens)
            query = parser.parse()
            
            # Generate execution plan
            plan = self._generate_execution_plan(query)
            
            return {
                "query": sql_query,
                "parameters": parameters or {},
                "parsed_query": {
                    "operation": query.operation.value if query.operation else "unknown",
                    "tables": [t.name for t in query.tables] if query.tables else [],
                    "columns": [c.name for c in query.columns] if query.columns else [],
                    "joins": [{"table": j.table.name, "type": j.type.value} for j in query.joins] if query.joins else [],
                    "where_conditions": len(query.where_conditions) if query.where_conditions else 0,
                    "order_by": [{"column": o.column.name, "direction": o.direction} for o in query.order_by] if query.order_by else [],
                    "group_by": [c.name for c in query.group_by.columns] if query.group_by and query.group_by.columns else [],
                    "limit": query.limit
                },
                "execution_plan": plan,
                "estimated_complexity": self._estimate_complexity(query)
            }
            
        except Exception as e:
            return {
                "error": f"SQL parsing error: {str(e)}",
                "query": sql_query,
                "parameters": parameters or {}
            }
    
    def validate_query(self, sql_query: str) -> Dict[str, Any]:
        """Validate a SQL query without executing it"""
        try:
            lexer = SQLLexer(sql_query)
            tokens = lexer.tokenize()
            parser = SQLParser(tokens)
            query = parser.parse()
            
            return {
                "valid": True,
                "query": sql_query,
                "operation": query.operation.value if query.operation else "unknown",
                "warnings": []
            }
            
        except Exception as e:
            return {
                "valid": False,
                "query": sql_query,
                "error": str(e),
                "warnings": []
            }
    
    def _apply_parameters(self, sql_query: str, parameters: Dict[str, Any]) -> str:
        """Apply parameters to a SQL query string"""
        # Simple parameter substitution
        result_query = sql_query
        
        for param, value in parameters.items():
            placeholder = f":{param}"
            if isinstance(value, str):
                # Quote string values
                result_query = result_query.replace(placeholder, f"'{value}'")
            elif value is None:
                result_query = result_query.replace(placeholder, "NULL")
            else:
                result_query = result_query.replace(placeholder, str(value))
        
        return result_query
    
    def _generate_execution_plan(self, query: SQLQuery) -> List[Dict[str, Any]]:
        """Generate execution plan for a query"""
        plan = []
        
        if query.operation == OperationType.SELECT:
            # Add table scan steps
            if query.tables:
                for table in query.tables:
                    plan.append({
                        "step": "table_scan",
                        "table": table.name,
                        "estimated_rows": "unknown"
                    })
            
            # Add join steps
            if query.joins:
                for join in query.joins:
                    plan.append({
                        "step": "join",
                        "type": join.type.value,
                        "table": join.table.name,
                        "condition": str(join.condition)
                    })
            
            # Add filter step
            if query.where_conditions:
                plan.append({
                    "step": "filter",
                    "conditions": len(query.where_conditions)
                })
            
            # Add sort step
            if query.order_by:
                plan.append({
                    "step": "sort",
                    "fields": [{"column": o.column.name, "direction": o.direction} for o in query.order_by]
                })
            
            # Add projection step
            if query.columns:
                plan.append({
                    "step": "projection",
                    "fields": [c.name for c in query.columns]
                })
        
        return plan
    
    def _estimate_complexity(self, query: SQLQuery) -> str:
        """Estimate query complexity"""
        complexity_score = 0
        
        # Base complexity
        complexity_score += 1
        
        # Add complexity for joins
        if query.joins:
            complexity_score += len(query.joins) * 2
        
        # Add complexity for where conditions
        if query.where_conditions:
            complexity_score += len(query.where_conditions)
        
        # Add complexity for aggregations
        if query.columns:
            for column in query.columns:
                if column.function and any(func in column.function.upper() for func in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']):
                    complexity_score += 1
        
        # Add complexity for subqueries (simplified check)
        if query.where_conditions:
            for condition in query.where_conditions:
                if "SELECT" in str(condition.value).upper():
                    complexity_score += 3
        
        if complexity_score <= 2:
            return "low"
        elif complexity_score <= 5:
            return "medium"
        else:
            return "high"


# Example usage and testing
if __name__ == "__main__":
    # This would be integrated with the main database engine
    pass
