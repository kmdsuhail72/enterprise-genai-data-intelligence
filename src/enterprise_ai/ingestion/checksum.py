"""Checksum calculation utility for uploaded files."""

import hashlib
from typing import BinaryIO


def calculate_sha256(file_obj: BinaryIO, chunk_size: int = 65536) -> str:
    """Calculate SHA-256 hash of a file-like object."""
    file_obj.seek(0)
    hasher = hashlib.sha256()
    while chunk := file_obj.read(chunk_size):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()

