"""Abstract base class for document extractors."""

import abc
from pathlib import Path
from typing import BinaryIO

from enterprise_ai.extraction.schemas import ExtractedDocument


class BaseExtractor(abc.ABC):
    """Abstract interface that all format-specific extractors implement."""

    @property
    @abc.abstractmethod
    def supported_extensions(self) -> set[str]:
        """Set of file extensions supported by this extractor (e.g., {'.pdf'})."""
        pass

    @abc.abstractmethod
    async def extract(
        self,
        file_obj: BinaryIO,
        filename: str,
        options: dict | None = None,
    ) -> ExtractedDocument:
        """Extract structured content from the provided file stream."""
        pass

    def supports(self, filename: str) -> bool:
        """Check if this extractor supports the given filename by extension."""
        ext = Path(filename).suffix.lower()
        return ext in self.supported_extensions
