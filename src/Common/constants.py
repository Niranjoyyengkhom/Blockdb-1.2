"""
IEDB Constants
==============
System-wide constants and configuration values.
"""

# Timeout settings
DEFAULT_TIMEOUT = 30  # seconds
CONNECTION_TIMEOUT = 10  # seconds
QUERY_TIMEOUT = 60  # seconds

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Supported database types
SUPPORTED_DATABASES = [
    "btree",
    "mongodb_style", 
    "sql",
    "archive",
    "multitenant"
]

# File extensions
FILE_EXTENSIONS = {
    "database": ".block⛓️",
    "table": ".chain🔗", 
    "schema": ".sch",
    "log": ".log",
    "backup": ".bak"
}

# API settings
API_VERSION = "v2.0.0"
DEFAULT_API_PORT = 4067
DEFAULT_HOST = "localhost"

# Security settings
DEFAULT_HASH_ALGORITHM = "SHA256"
DEFAULT_ENCRYPTION_ALGORITHM = "AES-256-GCM"
MIN_PASSWORD_LENGTH = 8
SESSION_TIMEOUT = 3600  # seconds (1 hour)

# Pagination settings
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Cache settings
DEFAULT_CACHE_TTL = 300  # seconds (5 minutes)
MAX_CACHE_SIZE = 1000  # items

# Data validation
MAX_STRING_LENGTH = 10000
MAX_ARRAY_SIZE = 1000
MAX_OBJECT_DEPTH = 10

# Tenant settings
MAX_TENANTS = 1000
MAX_DATABASES_PER_TENANT = 100
MAX_TABLES_PER_DATABASE = 500

# Logging settings
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "INFO"
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_LOG_FILES = 5

# AI settings
AI_QUERY_TIMEOUT = 30  # seconds
MAX_AI_CONTEXT_LENGTH = 4000  # characters
AI_CONFIDENCE_THRESHOLD = 0.7

# Storage settings
DEFAULT_STORAGE_PATH = "./Tenants_DB"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
BACKUP_RETENTION_DAYS = 30

# HTTP status codes commonly used
HTTP_STATUS_CODES = {
    "OK": 200,
    "CREATED": 201, 
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503
}

# Error codes
ERROR_CODES = {
    "UNKNOWN_ERROR": "E0000",
    "VALIDATION_ERROR": "E0001",
    "DATABASE_ERROR": "E0002", 
    "SECURITY_ERROR": "E0003",
    "AUTHENTICATION_ERROR": "E0004",
    "AUTHORIZATION_ERROR": "E0005",
    "ENCRYPTION_ERROR": "E0006",
    "TENANT_ERROR": "E0007",
    "CONFIGURATION_ERROR": "E0008",
    "CONNECTION_ERROR": "E0009"
}
