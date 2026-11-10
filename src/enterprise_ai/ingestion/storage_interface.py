"""Abstract storage interface for document artifacts."""

import abc
import uuid
from typing import BinaryIO


class StorageInterface(abc.ABC):
    """Abstract interface for document file persistence."""

    @abc.abstractmethod
    async def save(self, file_obj: BinaryIO, filename: str, document_id: uuid.UUID) -> str:
        """Persist a file stream and return its storage URI or absolute path."""
        pass

    @abc.abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Read bytes from storage path."""
        pass

    @abc.abstractmethod
    async def delete(self, storage_path: str) -> bool:
        """Remove file from storage."""
        pass

    @abc.abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """Check if file exists in storage."""
        pass

