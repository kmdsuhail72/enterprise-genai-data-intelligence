"""System-wide constants and configuration defaults for the Enterprise GenAI Platform."""

# Preserve the existing stringification behavior of these string-backed enums.
# ruff: noqa: UP042

from enum import Enum

from enterprise_ai import __version__

API_V1_PREFIX = "/api/v1"
APP_VERSION = __version__


class Environment(str, Enum):
    """Application runtime environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DocumentStatus(str, Enum):
    """Document lifecycle processing states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    """Role-based access control roles."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AccessPermission(str, Enum):
    """Document-level access permissions."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class LLMProvider(str, Enum):
    """Supported Large Language Model providers."""

    OLLAMA = "ollama"
    BEDROCK = "bedrock"
    OPENAI = "openai"
    GEMINI = "gemini"


class EmbeddingProvider(str, Enum):
    """Supported vector embedding providers."""

    OLLAMA = "ollama"
    BEDROCK = "bedrock"
    OPENAI = "openai"


class QueryType(str, Enum):
    """Intent classification for incoming natural language queries."""

    SEMANTIC = "semantic"
    FINANCIAL = "financial"
    TABULAR = "tabular"
    HYBRID = "hybrid"


# Default vector dimensions
EMBEDDING_DIMENSIONS: dict[str, int] = {
    "nomic-embed-text": 768,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "amazon.titan-embed-text-v2:0": 1024,
}

# Supported file extensions & MIME types
SUPPORTED_EXTENSIONS: set[str] = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
}

MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
DEFAULT_CHUNK_SIZE: int = 1000
DEFAULT_CHUNK_OVERLAP: int = 200
DEFAULT_TOP_K: int = 10
DEFAULT_RERANK_TOP_N: int = 5
