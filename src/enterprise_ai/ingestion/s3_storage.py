"""Amazon S3 storage implementation."""

import uuid
from typing import BinaryIO

from enterprise_ai.core.config import get_settings
from enterprise_ai.core.exceptions import FileNotFoundError_, StorageError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.ingestion.storage_interface import StorageInterface

logger = get_logger(__name__)


class S3Storage(StorageInterface):
    """Amazon S3 storage backend for AWS cloud deployments."""

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

