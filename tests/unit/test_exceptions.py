"""Tests for custom exceptions."""

import pytest

from enterprise_ai.core.exceptions import (
    AuthError,
    DocumentError,
    DocumentNotFoundError,
    DocumentValidationError,
    EmbeddingError,
    ExtractionError,
    FileSizeLimitError,
    InsufficientPermissionsError,
    InvalidCredentialsError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    OCRError,
    PIIError,
    PlatformError,
    RAGError,
    RetrievalError,
    StorageError,
    UnsupportedFileTypeError,
)


class TestExceptionHierarchy:
    """Test the exception class hierarchy."""

    def test_platform_error_base(self):
        err = PlatformError("test error", detail="extra detail")
        assert str(err) == "test error"
        assert err.message == "test error"
        assert err.detail == "extra detail"

    def test_platform_error_no_detail(self):
        err = PlatformError("test error")
        assert err.detail is None

    def test_document_errors_inherit_from_platform(self):
        assert issubclass(DocumentError, PlatformError)
        assert issubclass(DocumentNotFoundError, DocumentError)
        assert issubclass(DocumentValidationError, DocumentError)
        assert issubclass(UnsupportedFileTypeError, DocumentValidationError)
        assert issubclass(FileSizeLimitError, DocumentValidationError)

    def test_extraction_errors_inherit_from_platform(self):
        assert issubclass(ExtractionError, PlatformError)
        assert issubclass(OCRError, ExtractionError)

    def test_auth_errors_inherit_from_platform(self):
        assert issubclass(AuthError, PlatformError)
        assert issubclass(InvalidCredentialsError, AuthError)
        assert issubclass(InsufficientPermissionsError, AuthError)

    def test_llm_errors_inherit_from_platform(self):
        assert issubclass(LLMError, PlatformError)
        assert issubclass(LLMProviderError, LLMError)
        assert issubclass(LLMTimeoutError, LLMError)
        assert issubclass(LLMRateLimitError, LLMError)

    def test_rag_errors_inherit_from_platform(self):
        assert issubclass(RAGError, PlatformError)
        assert issubclass(RetrievalError, RAGError)
        assert issubclass(EmbeddingError, RAGError)

    def test_storage_error_inherits_from_platform(self):
        assert issubclass(StorageError, PlatformError)

    def test_pii_error_inherits_from_platform(self):
        assert issubclass(PIIError, PlatformError)

    def test_exceptions_are_catchable(self):
        with pytest.raises(PlatformError):
            raise DocumentNotFoundError("doc not found")

        with pytest.raises(DocumentError):
            raise UnsupportedFileTypeError("bad type")

    def test_exception_message_preserved(self):
        err = LLMTimeoutError("timeout after 30s", detail="provider=openai")
        assert err.message == "timeout after 30s"
        assert err.detail == "provider=openai"
