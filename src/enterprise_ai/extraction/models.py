"""Standard data models for document extraction results."""

import uuid
from typing import Any
from pydantic import BaseModel, Field


class ExtractedTable(BaseModel):
    """Structured representation of an extracted table."""

    table_index: int = Field(..., description="Zero-based table index within the page/sheet")
    headers: list[str] = Field(default_factory=list, description="Column header labels")
    rows: list[list[Any]] = Field(default_factory=list, description="Row values as 2D list")
    caption: str | None = Field(default=None, description="Table title, caption, or sheet name")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context (e.g. bbox, sheet)")

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.headers) if self.headers else (len(self.rows[0]) if self.rows else 0)

    def to_markdown(self) -> str:
        """Render table as a standard markdown table string."""
        if not self.headers and not self.rows:
            return ""

        headers = self.headers if self.headers else [f"Col {i+1}" for i in range(self.column_count)]
        header_line = "| " + " | ".join(str(h).strip() for h in headers) + " |"
        separator_line = "| " + " | ".join("---" for _ in headers) + " |"

        data_lines = []
        for row in self.rows:
            # Pad row if shorter than headers
            padded_row = list(row) + [""] * (len(headers) - len(row))
            data_lines.append("| " + " | ".join(str(cell).strip().replace("\n", " ") for cell in padded_row[:len(headers)]) + " |")

        return "\n".join([header_line, separator_line] + data_lines)


class ExtractedPage(BaseModel):
    """Extracted content from a single page, slide, or sheet."""

    page_number: int = Field(..., description="1-based page or sheet sequence number")
    raw_text: str = Field(..., description="Raw text extracted from page")
    cleaned_text: str | None = Field(default=None, description="Cleaned, normalized text")
    extraction_method: str = Field(..., description="Method used: fitz, openpyxl, pandas, python-docx, ocr")
    tables: list[ExtractedTable] = Field(default_factory=list, description="Tables identified on this page")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Page-level metadata (dimensions, orientation, etc.)")


class ExtractedDocument(BaseModel):
    """Complete extracted document payload containing all pages and summary metadata."""

    document_id: uuid.UUID = Field(..., description="Unique document UUID")
    filename: str = Field(..., description="Original filename with extension")
    content_type: str = Field(..., description="MIME type or file extension identifier")
    total_pages: int = Field(..., description="Total pages or sheets extracted")
    pages: list[ExtractedPage] = Field(default_factory=list, description="List of per-page extracted contents")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document-level metadata (author, created date, etc.)")

    @property
    def full_text(self) -> str:
        """Concatenate text across all pages with page markers."""
        return "\n\n".join(
            f"--- [Page {page.page_number}] ---\n{page.raw_text}"
            for page in self.pages
            if page.raw_text.strip()
        )

    @property
    def total_tables(self) -> int:
        return sum(len(page.tables) for page in self.pages)

