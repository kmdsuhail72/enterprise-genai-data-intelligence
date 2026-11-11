"""Microsoft Excel (.xlsx, .xls) extractor processing multi-sheet workbooks."""

import io
from typing import BinaryIO

import pandas as pd

from enterprise_ai.core.exceptions import ExtractionError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.extraction.base_extractor import BaseExtractor
from enterprise_ai.extraction.schemas import ExtractedDocument, ExtractedPage
from enterprise_ai.extraction.table_extractor import TableExtractor

logger = get_logger(__name__)


class ExcelExtractor(BaseExtractor):
    """Extracts structured worksheets and tables from Excel workbooks."""

    @property
    def supported_extensions(self) -> set[str]:
        return {".xlsx", ".xls"}

    async def extract(
        self,
        file_obj: BinaryIO,
        filename: str,
        options: dict | None = None,
    ) -> ExtractedDocument:
        """Extract all worksheets as structured tables and textual summaries."""
        file_obj.seek(0)
        file_bytes = file_obj.read()
        file_obj.seek(0)

        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        except Exception as exc:
            logger.error("excel_read_failed", filename=filename, error=str(exc))
            raise ExtractionError(f"Failed to read Excel file '{filename}': {exc}")

        pages: list[ExtractedPage] = []
        sheet_names = excel_file.sheet_names
        total_pages = len(sheet_names)

        logger.info("excel_extraction_started", filename=filename, total_sheets=total_pages)

        for sheet_idx, sheet_name in enumerate(sheet_names):
            page_num = sheet_idx + 1
            try:
                df = excel_file.parse(sheet_name=sheet_name)
                # Drop rows/columns that are entirely NaN
                df = df.dropna(how="all").dropna(axis=1, how="all")

                headers = [str(col).strip() for col in df.columns]
                rows = df.values.tolist()

                # Clean NaN representations in rows
                cleaned_rows = [[str(val) if pd.notna(val) else "" for val in row] for row in rows]

                # Convert to ExtractedTable
                table = TableExtractor.from_rows(
                    rows=[headers] + cleaned_rows,
                    page_number=page_num,
                    table_index=1,
                    sheet_name=sheet_name,
                )

                tables = [table] if table else []

                # Build narrative text representation of worksheet for RAG semantic search
                sheet_summary_lines = [
                    f"# Sheet: {sheet_name}",
                    f"Dimensions: {len(df)} rows x {len(df.columns)} columns\n",
                ]
                if table:
                    sheet_summary_lines.append(table.to_markdown())

                sheet_text = "\n\n".join(sheet_summary_lines)

                page = ExtractedPage(
                    page_number=page_num,
                    raw_text=sheet_text,
                    cleaned_text=sheet_text,
                    extraction_method="excel",
                    tables=tables,
                    metadata={
                        "sheet_name": sheet_name,
                        "row_count": len(df),
                        "column_count": len(df.columns),
                    },
                )
                pages.append(page)

            except Exception as exc:
                logger.warning("excel_sheet_extraction_failed", sheet=sheet_name, error=str(exc))
                empty_page = ExtractedPage(
                    page_number=page_num,
                    raw_text="",
                    cleaned_text="",
                    extraction_method="excel",
                    metadata={"sheet_name": sheet_name, "error": str(exc)},
                )
                pages.append(empty_page)

        return ExtractedDocument(
            filename=filename,
            file_type="excel",
            total_pages=total_pages,
            pages=pages,
            metadata={
                "sheet_names": sheet_names,
                "format": "EXCEL",
            },
        )
