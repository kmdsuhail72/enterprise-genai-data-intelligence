"""Local filesystem storage implementation."""

import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from enterprise_ai.core.config import get_settings
from enterprise_ai.core.exceptions import FileNotFoundError_, StorageError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.ingestion.storage_interface import StorageInterface

logger = get_logger(__name__)


class LocalStorage(StorageInterface):
    """Local filesystem storage backend for development environments."""

    def __init__(self, base_path: str | None = None):
        settings = get_settings()
        self.base_path = Path(base_path or settings.storage_local_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, file_obj: BinaryIO, filename: str, document_id: uuid.UUID) -> str:
        try:
            doc_dir = self.base_path / str(document_id)
            doc_dir.mkdir(parents=True, exist_ok=True)
            target_file = doc_dir / filename

            file_obj.seek(0)
            with open(target_file, "wb") as out:
                shutil.copyfileobj(file_obj, out)

            logger.info("file_saved_locally", path=str(target_file), document_id=str(document_id))
            return str(target_file)
        except Exception as exc:
            logger.error("file_save_failed", error=str(exc), filename=filename)
            raise StorageError(f"Failed to save file '{filename}' to local storage: {exc}")

    async def read(self, storage_path: str) -> bytes:
        path = Path(storage_path)
        if not path.is_file():
            raise FileNotFoundError_(f"File not found at '{storage_path}'")
        return path.read_bytes()

    async def delete(self, storage_path: str) -> bool:
        path = Path(storage_path)
        if path.is_file():
            path.unlink()
            parent = path.parent
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
            return True
        return False

    async def exists(self, storage_path: str) -> bool:
        return Path(storage_path).is_file()

