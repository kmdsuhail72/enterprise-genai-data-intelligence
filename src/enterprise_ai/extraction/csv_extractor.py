"""Delimited text (CSV, TSV) extractor with delimiter auto-detection."""

import csv
import io
from typing import BinaryIO
import pandas as pd

from enterprise_ai.core.exceptions import ExtractionError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.extraction.base_extractor import BaseExtractor
from enterprise_ai.extraction.schemas import ExtractedDocument, ExtractedPage, ExtractedTable
from enterprise_ai.extraction.table_extractor import TableExtractor

logger = get_logger(__name__)


class CSVExtractor(BaseExtractor):
    """Extracts tabular data and text representation from CSV and delimited text files."""

    @property
    def supported_extensions(self) -> set[str]:
        return {".csv", ".tsv"}

    async def extract(
        self,
        file_obj: BinaryIO,
        filename: str,
        options: dict | None = None,
    ) -> ExtractedDocument:
        """Parse CSV content with delimiter detection and construct structured output."""
        file_obj.seek(0)
        raw_bytes = file_obj.read()
        file_obj.seek(0)

        # Detect encoding and decode
        encoding = "utf-8"
        try:
            sample_str = raw_bytes[:4096].decode("utf-8")
        except UnicodeDecodeError:
            try:
                sample_str = raw_bytes[:4096].decode("latin-1")
                encoding = "latin-1"
            except Exception:
                sample_str = raw_bytes[:4096].decode("utf-8", errors="replace")

        # Detect delimiter
        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample_str)
            delimiter = dialect.delimiter
        except Exception:
            if "\t" in sample_str:
                delimiter = "\t"
            elif ";" in sample_str:
                delimiter = ";"

        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), delimiter=delimiter, encoding=encoding)
            df = df.dropna(how="all").dropna(axis=1, how="all")
        except Exception as exc:
            logger.error("csv_read_failed", filename=filename, error=str(exc))
            raise ExtractionError(f"Failed to read CSV '{filename}': {exc}")

        headers = [str(col).strip() for col in df.columns]
        rows = [[str(val) if pd.notna(val) else "" for val in row] for row in df.values.tolist()]

        table = TableExtractor.from_rows(
            rows=[headers] + rows,
            page_number=1,
            table_index=1,
            title=filename,
        )

        tables = [table] if table else []

        # Narrative summary for RAG
        summary_lines = [
            f"# CSV File: {filename}",
            f"Delimiter: '{delimiter}' | Dimensions: {len(df)} rows x {len(df.columns)} columns\n",
        ]
        if table:
            summary_lines.append(table.to_markdown())

        text_content = "\n\n".join(summary_lines)

        page = ExtractedPage(
            page_number=1,
            raw_text=text_content,
            cleaned_text=text_content,
            extraction_method="csv",
            tables=tables,
            metadata={
                "row_count": len(df),
                "column_count": len(df.columns),
                "delimiter": delimiter,
                "encoding": encoding,
            },
        )

        return ExtractedDocument(
            filename=filename,
            file_type="csv",
            total_pages=1,
            pages=[page],
            metadata={
                "format": "CSV",
                "row_count": len(df),
                "column_count": len(df.columns),
            },
        )
