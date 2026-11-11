"""Document upload coordinator handling ingestion pipeline handoff."""

import uuid
from typing import BinaryIO

from enterprise_ai.core.logging import get_logger
from enterprise_ai.ingestion.checksum import calculate_sha256
from enterprise_ai.ingestion.file_validator import FileValidationResult, FileValidator
from enterprise_ai.ingestion.local_storage import LocalStorage
from enterprise_ai.ingestion.storage_interface import StorageInterface

logger = get_logger(__name__)


class UploadService:
    """Handles file validation, hashing, and storage handoff."""

    def __init__(
        self,
        validator: FileValidator | None = None,
        storage: StorageInterface | None = None,
    ):
        self.validator = validator or FileValidator()
        self.storage = storage or LocalStorage()

    async def handle_upload(
        self,
        file_obj: BinaryIO,
        filename: str,
        document_id: uuid.UUID,
    ) -> tuple[FileValidationResult, str, str]:
        """Validate, compute checksum, and persist file."""
        # Validate
        validation_result = self.validator.validate(file_obj, filename)

        # Checksum
        checksum = calculate_sha256(file_obj)

        # Storage
        storage_path = await self.storage.save(file_obj, filename, document_id)

        return validation_result, storage_path, checksum

