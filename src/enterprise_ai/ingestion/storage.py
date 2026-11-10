"""Storage abstraction layer for documents (local filesystem and AWS S3)."""

import abc
import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.config import get_settings
from app.core.exceptions import StorageError, FileNotFoundError_
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageBackend(abc.ABC):
    """Abstract interface for document file persistence."""

    @abc.abstractmethod
    async def save(self, file_obj: BinaryIO, filename: str, document_id: uuid.UUID) -> str:
        """Persist a file stream and return its storage URI or path."""
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


class LocalStorage(StorageBackend):
    """Local filesystem storage backend for Stage A development."""

    def __init__(self, base_path: str | None = None):
        settings = get_settings()
        self.base_path = Path(base_path or settings.storage_local_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, file_obj: BinaryIO, filename: str, document_id: uuid.UUID) -> str:
        try:
            # Namespace by document ID to avoid collisions
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
            # Remove directory if empty
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
            return True
        return False

    async def exists(self, storage_path: str) -> bool:
        return Path(storage_path).is_file()


class S3Storage(StorageBackend):
    """Amazon S3 storage backend for Stage B cloud deployment."""

    def __init__(self, bucket_name: str | None = None, region: str | None = None):
        settings = get_settings()
        self.bucket_name = bucket_name or settings.aws_s3_bucket
        self.region = region or settings.aws_region
        if not self.bucket_name:
            logger.warning("s3_storage_initialized_without_bucket")

    async def save(self, file_obj: BinaryIO, filename: str, document_id: uuid.UUID) -> str:
        if not self.bucket_name:
            raise StorageError("AWS_S3_BUCKET is not configured.")
        import boto3
        from botocore.exceptions import ClientError

        s3_key = f"documents/{document_id}/{filename}"
        s3 = boto3.client("s3", region_name=self.region)
        try:
            file_obj.seek(0)
            s3.upload_fileobj(file_obj, self.bucket_name, s3_key)
            return f"s3://{self.bucket_name}/{s3_key}"
        except ClientError as exc:
            raise StorageError(f"S3 upload error: {exc}")

    async def read(self, storage_path: str) -> bytes:
        import boto3
        from botocore.exceptions import ClientError

        if not storage_path.startswith("s3://"):
            raise StorageError(f"Invalid S3 URI: {storage_path}")

        path_part = storage_path.replace("s3://", "")
        bucket, key = path_part.split("/", 1)
        s3 = boto3.client("s3", region_name=self.region)
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            raise FileNotFoundError_(f"S3 object not found or error: {exc}")

    async def delete(self, storage_path: str) -> bool:
        import boto3
        if not storage_path.startswith("s3://"):
            return False
        path_part = storage_path.replace("s3://", "")
        bucket, key = path_part.split("/", 1)
        s3 = boto3.client("s3", region_name=self.region)
        s3.delete_object(Bucket=bucket, Key=key)
        return True

    async def exists(self, storage_path: str) -> bool:
        import boto3
        from botocore.exceptions import ClientError
        if not storage_path.startswith("s3://"):
            return False
        path_part = storage_path.replace("s3://", "")
        bucket, key = path_part.split("/", 1)
        s3 = boto3.client("s3", region_name=self.region)
        try:
            s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False


def get_storage_backend() -> StorageBackend:
    """Factory creating configured storage backend."""
    settings = get_settings()
    if settings.storage_backend.lower() == "s3":
        return S3Storage()
    return LocalStorage()

