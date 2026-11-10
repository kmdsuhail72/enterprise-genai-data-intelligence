"""File validation service verifying MIME types, magic bytes, and size boundaries."""

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from enterprise_ai.core.constants import MAX_FILE_SIZE_BYTES, SUPPORTED_EXTENSIONS
from enterprise_ai.core.exceptions import FileSizeLimitError, UnsupportedFileTypeError
from enterprise_ai.core.logging import get_logger

logger = get_logger(__name__)

# Known file signatures (magic bytes)
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    ".pdf": [b"%PDF"],
    ".docx": [b"PK\x03\x04"],
    ".xlsx": [b"PK\x03\x04"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".tiff": [b"II*\x00", b"MM\x00*"],
}

MIME_TYPE_MAP: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".csv": "text/csv",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tiff": "image/tiff",
}


@dataclass(frozen=True)
class FileValidationResult:
    """Output metadata from file validation."""
    filename: str
    extension: str
    mime_type: str
    file_size_bytes: int
    is_valid: bool = True


class FileValidator:
    """Validates uploaded files for enterprise compliance."""

    def __init__(self, max_size_bytes: int = MAX_FILE_SIZE_BYTES):
        self.max_size_bytes = max_size_bytes

    def validate(self, file_obj: BinaryIO, filename: str) -> FileValidationResult:
        """Validate extension, size, and magic bytes."""
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"File type '{ext}' is not supported. Allowed: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        # Check file size
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(0)

        if size == 0:
            raise UnsupportedFileTypeError(f"File '{filename}' is empty.")

        if size > self.max_size_bytes:
            raise FileSizeLimitError(
                f"File '{filename}' exceeds maximum allowed size ({size} > {self.max_size_bytes} bytes)."
            )

        # Validate magic bytes where applicable
        if ext in MAGIC_SIGNATURES:
            header = file_obj.read(16)
            file_obj.seek(0)
            valid_sig = any(header.startswith(sig) for sig in MAGIC_SIGNATURES[ext])
            if not valid_sig:
                raise UnsupportedFileTypeError(
                    f"File '{filename}' content header does not match expected extension signature '{ext}'."
                )

        mime = MIME_TYPE_MAP.get(ext, "application/octet-stream")
        return FileValidationResult(
            filename=filename,
            extension=ext,
            mime_type=mime,
            file_size_bytes=size,
            is_valid=True,
        )
