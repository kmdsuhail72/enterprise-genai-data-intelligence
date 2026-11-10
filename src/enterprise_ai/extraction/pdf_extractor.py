"""High-performance PDF extractor utilizing PyMuPDF with OCR fallback for scanned pages."""

import io
from pathlib import Path
from typing import BinaryIO

from enterprise_ai.core.exceptions import ExtractionError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.extraction.base_extractor import BaseExtractor
from enterprise_ai.extraction.layout_analyzer import LayoutAnalyzer
from enterprise_ai.extraction.ocr_engine import OCREngine
from enterprise_ai.extraction.schemas import ExtractedDocument, ExtractedPage, ExtractedTable
from enterprise_ai.extraction.table_extractor import TableExtractor

logger = get_logger(__name__)


class PDFExtractor(BaseExtractor):
    """Extracts text, structural tables, and metadata from PDF files."""

    def __init__(self, ocr_engine: OCREngine | None = None, min_char_threshold: int = 50):
        self.ocr_engine = ocr_engine or OCREngine()
        self.min_char_threshold = min_char_threshold

    @property
    def supported_extensions(self) -> set[str]:
        return {".pdf"}

    async def extract(
        self,
        file_obj: BinaryIO,
        filename: str,
        options: dict | None = None,
    ) -> ExtractedDocument:
        """Extract all pages, tables, and metadata from a PDF file."""
        options = options or {}
        force_ocr = options.get("force_ocr", False)

        try:
            import pymupdf as fitz
        except ImportError:
            raise ExtractionError("PyMuPDF (pymupdf) is not installed. Run `pip install pymupdf`.")

        file_obj.seek(0)
        file_bytes = file_obj.read()
        file_obj.seek(0)

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            logger.error("pdf_open_failed", filename=filename, error=str(exc))
            raise ExtractionError(f"Failed to open PDF '{filename}': {exc}")

        pages: list[ExtractedPage] = []
        total_pages = len(doc)

        logger.info("pdf_extraction_started", filename=filename, total_pages=total_pages)

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 1. Native text extraction
            native_text = page.get_text("text").strip()
            images_list = page.get_images(full=True)
            image_count = len(images_list)

            # 2. Native table detection via PyMuPDF table finder
            tables: list[ExtractedTable] = []
            try:
                tabs = page.find_tables()
                for t_idx, tab in enumerate(tabs):
                    matrix = tab.extract()
                    if matrix:
                        extracted_tbl = TableExtractor.from_rows(
                            rows=matrix,
                            page_number=page_num,
                            table_index=t_idx + 1,
                        )
                        if extracted_tbl:
                            tables.append(extracted_tbl)
            except Exception as exc:
                logger.debug("table_finder_error", page=page_num, error=str(exc))

            # 3. Determine if OCR is needed (scanned page or low text density)
            needs_ocr = force_ocr or (len(native_text) < self.min_char_threshold and image_count > 0)
            has_ocr = False
            final_text = native_text
            method = "native_pdf"

            if needs_ocr and self.ocr_engine.is_available:
                try:
                    # Render page to pixmap image
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    ocr_text, ocr_boxes = await self.ocr_engine.ocr_image(img_bytes)
                    if ocr_text.strip():
                        final_text = ocr_text.strip()
                        has_ocr = True
                        method = "ocr_fallback" if not force_ocr else "ocr"
                        logger.info("pdf_page_ocr_applied", page=page_num, char_count=len(final_text))
                except Exception as exc:
                    logger.warning("pdf_ocr_fallback_failed", page=page_num, error=str(exc))

            # Also check text for markdown tables if find_tables didn't find any
            if not tables and "|" in final_text:
                markdown_tables = TableExtractor.parse_markdown_table(final_text, page_number=page_num)
                tables.extend(markdown_tables)

            extracted_page = ExtractedPage(
                page_number=page_num,
                raw_text=native_text,
                cleaned_text=final_text,
                extraction_method=method,
                tables=tables,
                has_ocr=has_ocr,
                metadata={
                    "native_char_count": len(native_text),
                    "image_count": image_count,
                    "rect": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
                },
            )
            pages.append(extracted_page)

        # Document-level metadata
        pdf_metadata = doc.metadata or {}
        doc.close()

        logger.info(
            "pdf_extraction_completed",
            filename=filename,
            pages=len(pages),
            total_tables=sum(len(p.tables) for p in pages),
        )

        return ExtractedDocument(
            filename=filename,
            file_type="pdf",
            total_pages=total_pages,
            pages=pages,
            metadata={
                "title": pdf_metadata.get("title", ""),
                "author": pdf_metadata.get("author", ""),
                "subject": pdf_metadata.get("subject", ""),
                "creator": pdf_metadata.get("creator", ""),
                "format": "PDF",
            },
        )
