"""Image and scanned document extractor with OCR engine integration."""

import io
from typing import BinaryIO
from PIL import Image

from enterprise_ai.core.exceptions import ExtractionError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.extraction.base_extractor import BaseExtractor
from enterprise_ai.extraction.ocr_engine import OCREngine
from enterprise_ai.extraction.schemas import ExtractedDocument, ExtractedPage, ExtractedTable
from enterprise_ai.extraction.table_extractor import TableExtractor

logger = get_logger(__name__)


class ImageExtractor(BaseExtractor):
    """Extracts text, annotations, and tables from standalone images using OCR."""

    def __init__(self, ocr_engine: OCREngine | None = None):
        self.ocr_engine = ocr_engine or OCREngine()

    @property
    def supported_extensions(self) -> set[str]:
        return {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}

    async def extract(
        self,
        file_obj: BinaryIO,
        filename: str,
        options: dict | None = None,
    ) -> ExtractedDocument:
        """Extract text and metadata from image file."""
        file_obj.seek(0)
        img_bytes = file_obj.read()
        file_obj.seek(0)

        try:
            image = Image.open(io.BytesIO(img_bytes))
            width, height = image.size
            img_format = image.format or "IMAGE"
        except Exception as exc:
            logger.error("image_open_failed", filename=filename, error=str(exc))
            raise ExtractionError(f"Failed to open image '{filename}': {exc}")

        # Perform OCR
        ocr_text = ""
        ocr_boxes: list[dict] = []
        if self.ocr_engine.is_available:
            try:
                ocr_text, ocr_boxes = await self.ocr_engine.ocr_image(img_bytes)
            except Exception as exc:
                logger.warning("ocr_image_failed", filename=filename, error=str(exc))

        # Check for tables in OCR output
        tables: list[ExtractedTable] = []
        if ocr_text and "|" in ocr_text:
            tables = TableExtractor.parse_markdown_table(ocr_text, page_number=1)

        page = ExtractedPage(
            page_number=1,
            raw_text=ocr_text,
            cleaned_text=ocr_text,
            extraction_method="ocr",
            tables=tables,
            has_ocr=True,
            metadata={
                "width": width,
                "height": height,
                "format": img_format,
                "detected_boxes": len(ocr_boxes),
            },
        )

        return ExtractedDocument(
            filename=filename,
            file_type="image",
            total_pages=1,
            pages=[page],
            metadata={
                "dimensions": f"{width}x{height}",
                "format": img_format,
            },
        )
