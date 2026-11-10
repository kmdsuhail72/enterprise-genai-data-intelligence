"""Custom exception hierarchy for the Enterprise GenAI Data Intelligence Platform.

Every exception inherits from :class:`PlatformError` so that a single
``except PlatformError`` handler can catch all domain-specific errors while
still allowing fine-grained handling where needed.
"""


# ── Base ─────────────────────────────────────────────────────────────────────


class PlatformError(Exception):
    """Base exception for all platform errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class ApplicationError(PlatformError):
    """Base class for application-level failures."""


class ConfigurationError(ApplicationError):
    """Application configuration is missing or invalid for an operation."""


class ValidationError(ApplicationError):
    """An application-level value failed validation."""


# ── Document Errors ──────────────────────────────────────────────────────────


class DocumentError(PlatformError):
    """Base for document-related errors."""


class DocumentNotFoundError(DocumentError):
    """Requested document was not found."""


class DocumentValidationError(DocumentError):
    """Document failed validation checks."""


class UnsupportedFileTypeError(DocumentValidationError):
    """The uploaded file type is not supported."""


class FileSizeLimitError(DocumentValidationError):
    """The uploaded file exceeds the allowed size limit."""


# ── Extraction Errors ────────────────────────────────────────────────────────


class ExtractionError(PlatformError):
    """Base for content-extraction errors."""


class OCRError(ExtractionError):
    """OCR processing failed."""


class TableExtractionError(ExtractionError):
    """Table extraction from a document page failed."""


# ── Database Errors ──────────────────────────────────────────────────────────


class DatabaseError(PlatformError):
    """Base for database-layer errors."""


class ExternalProviderError(PlatformError):
    """Base for failures returned by an external service provider."""


class RecordNotFoundError(DatabaseError):
    """Expected record was not found in the database."""


class DuplicateRecordError(DatabaseError):
    """A record with the same unique constraint already exists."""


# ── Auth Errors ──────────────────────────────────────────────────────────────


class AuthError(PlatformError):
    """Base for authentication / authorisation errors."""


class InvalidCredentialsError(AuthError):
    """Supplied credentials are invalid."""


class InsufficientPermissionsError(AuthError):
    """User does not have the required permissions for this action."""


class TokenExpiredError(AuthError):
    """The JWT token has expired."""


# ── LLM Errors ──────────────────────────────────────────────────────────────


class LLMError(PlatformError):
    """Base for LLM-related errors."""


class LLMProviderError(LLMError):
    """The LLM provider returned an error response."""


class LLMTimeoutError(LLMError):
    """The LLM request timed out."""


class LLMRateLimitError(LLMError):
    """The LLM provider's rate limit has been exceeded."""


# ── RAG Errors ──────────────────────────────────────────────────────────────


class RAGError(PlatformError):
    """Base for RAG pipeline errors."""


class RetrievalError(RAGError):
    """Error during the retrieval phase of the RAG pipeline."""


class EmbeddingError(RAGError):
    """Error while generating vector embeddings."""


# ── Storage Errors ──────────────────────────────────────────────────────────


class StorageError(PlatformError):
    """Base for file-storage errors."""


class FileUploadError(StorageError):
    """File upload to the storage backend failed."""


class FileNotFoundError_(StorageError):  # noqa: N801, N818
    """Requested file was not found in the storage backend.

    Named with a trailing underscore to avoid shadowing the built-in
    :class:`FileNotFoundError`.
    """


# ── PII Errors ──────────────────────────────────────────────────────────────


class PIIError(PlatformError):
    """Error during PII detection or masking."""
