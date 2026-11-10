"""Extraction router delegating file parsing to format-specific extractors."""

from pathlib import Path
from typing import BinaryIO

from enterprise_ai.core.exceptions import UnsupportedFileTypeError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.extraction.base_extractor import BaseExtractor
from enterprise_ai.extraction.csv_extractor import CSVExtractor
from enterprise_ai.extraction.docx_extractor import DocxExtractor
from enterprise_ai.extraction.excel_extractor import ExcelExtractor
from enterprise_ai.extraction.image_extractor import ImageExtractor
from enterprise_ai.extraction.ocr_engine import OCREngine
from enterprise_ai.extraction.pdf_extractor import PDFExtractor
from enterprise_ai.extraction.schemas import ExtractedDocument

logger = get_logger(__name__)


class ExtractionRouter:
    """Dispatches extraction requests to appropriate format-specific extractors."""

    def __init__(self, ocr_engine: OCREngine | None = None):
        self.ocr_engine = ocr_engine or OCREngine()
        self._extractors: list[BaseExtractor] = [
            PDFExtractor(ocr_engine=self.ocr_engine),
            DocxExtractor(),
            ExcelExtractor(),
            CSVExtractor(),
            ImageExtractor(ocr_engine=self.ocr_engine),
        ]

    def get_extractor(self, filename: str) -> BaseExtractor:
        """Find an extractor capable of handling the file."""
        for extractor in self._extractors:
            if extractor.supports(filename):
                return extractor

        ext = Path(filename).suffix.lower()
        raise UnsupportedFileTypeError(f"No extractor registered for file extension '{ext}'.")

    async def extract(
        self,
        file_obj: BinaryIO,
        filename: str,
        options: dict | None = None,
    ) -> ExtractedDocument:
        """Route file to appropriate extractor and return standardized ExtractedDocument."""
        extractor = self.get_extractor(filename)
        logger.info(
            "routing_document_extraction",
            filename=filename,
            extractor=extractor.__class__.__name__,
        )
        return await extractor.extract(file_obj, filename, options=options)


# Default global router instance
_default_router: ExtractionRouter | None = None


def get_extraction_router() -> ExtractionRouter:
    """Return singleton ExtractionRouter instance."""
    global _default_router
    if _default_router is None:
        _default_router = ExtractionRouter()
    return _default_router
