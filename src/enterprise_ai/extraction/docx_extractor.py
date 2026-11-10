"""Microsoft Word (.docx) document extractor preserving headings, paragraphs, and tables."""

import io
from typing import BinaryIO

from enterprise_ai.core.exceptions import ExtractionError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.extraction.base_extractor import BaseExtractor
from enterprise_ai.extraction.schemas import ExtractedDocument, ExtractedPage, ExtractedTable
from enterprise_ai.extraction.table_extractor import TableExtractor

logger = get_logger(__name__)


class DocxExtractor(BaseExtractor):
    """Extracts text, headings, and tables from .docx documents."""

    @property
    def supported_extensions(self) -> set[str]:
        return {".docx"}

    async def extract(
        self,
        file_obj: BinaryIO,
        filename: str,
        options: dict | None = None,
    ) -> ExtractedDocument:
        """Extract paragraphs and tables from a Word document."""
        try:
            import docx
        except ImportError:
            raise ExtractionError("python-docx is not installed. Run `pip install python-docx`.")

        file_obj.seek(0)
        file_bytes = file_obj.read()
        file_obj.seek(0)

        try:
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as exc:
            logger.error("docx_open_failed", filename=filename, error=str(exc))
            raise ExtractionError(f"Failed to open Word document '{filename}': {exc}")

        # Extract paragraphs with heading markers
        paragraph_texts: list[str] = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if p.style.name.startswith("Heading"):
                # Markdown heading formatting
                level = 1
                try:
                    level = int(p.style.name.replace("Heading", "").strip())
                except ValueError:
                    pass
                paragraph_texts.append(f"{'#' * level} {text}")
            else:
                paragraph_texts.append(text)

        # Extract tables
        tables: list[ExtractedTable] = []
        for t_idx, table in enumerate(doc.tables):
            matrix: list[list[str]] = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                matrix.append(row_cells)

            if matrix:
                extracted_tbl = TableExtractor.from_rows(
                    rows=matrix,
                    page_number=1,
                    table_index=t_idx + 1,
                )
                if extracted_tbl:
                    tables.append(extracted_tbl)

        combined_text = "\n\n".join(paragraph_texts)

        # Append table markdown summaries to text for complete searchability
        if tables:
            table_summaries = "\n\n".join(t.to_text_summary() for t in tables)
            combined_text = f"{combined_text}\n\n{table_summaries}" if combined_text else table_summaries

        page = ExtractedPage(
            page_number=1,
            raw_text=combined_text,
            cleaned_text=combined_text,
            extraction_method="docx",
            tables=tables,
            metadata={
                "paragraph_count": len(paragraph_texts),
                "table_count": len(tables),
            },
        )

        return ExtractedDocument(
            filename=filename,
            file_type="docx",
            total_pages=1,
            pages=[page],
            metadata={
                "format": "DOCX",
                "table_count": len(tables),
            },
        )
