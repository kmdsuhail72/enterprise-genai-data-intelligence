"""Standardized data contracts for document extraction outputs."""

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class ExtractedTable:
    """Extracted tabular structure from a document page or worksheet."""
    table_index: int
    page_number: int
    headers: list[str]
    rows: list[list[Any]]
    title: str | None = None
    sheet_name: str | None = None
    dataframe_json: str | None = None

    def to_markdown(self) -> str:
        """Convert extracted table into GitHub Flavored Markdown."""
        if not self.headers and not self.rows:
            return ""

        headers = self.headers if self.headers else [f"Col_{i+1}" for i in range(len(self.rows[0]) if self.rows else 0)]
        header_line = "| " + " | ".join(str(h) for h in headers) + " |"
        sep_line = "| " + " | ".join("---" for _ in headers) + " |"

        row_lines = []
        for row in self.rows:
            row_str = "| " + " | ".join(str(cell) if cell is not None else "" for cell in row) + " |"
            row_lines.append(row_str)

        return "\n".join([header_line, sep_line] + row_lines)

    def to_text_summary(self) -> str:
        """Render a readable summary for LLM context."""
        title_str = f"Table {self.table_index}" + (f" ({self.title})" if self.title else "")
        return f"[{title_str} on Page {self.page_number}]\n{self.to_markdown()}"


@dataclass
class ExtractedPage:
    """Extracted text and structural elements from a single page or sheet."""
    page_number: int
    raw_text: str
    cleaned_text: str
    extraction_method: str  # native_pdf, ocr, docx, excel, csv
    tables: list[ExtractedTable] = field(default_factory=list)
    images: list[dict[str, Any]] = field(default_factory=list)
    char_count: int = 0
    word_count: int = 0
    has_ocr: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.char_count and self.raw_text:
            self.char_count = len(self.raw_text)
        if not self.word_count and self.raw_text:
            self.word_count = len(self.raw_text.split())


@dataclass
class ExtractedDocument:
    """Normalized document representation output by the extraction router."""
    filename: str
    file_type: str
    total_pages: int
    pages: list[ExtractedPage] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    document_id: uuid.UUID | None = None

    def get_full_text(self) -> str:
        """Concatenate cleaned text across all pages in reading order."""
        return "\n\n".join(page.cleaned_text for page in self.pages if page.cleaned_text.strip())

    def get_tables(self) -> list[ExtractedTable]:
        """Collect all extracted tables from every page."""
        all_tables: list[ExtractedTable] = []
        for page in self.pages:
            all_tables.extend(page.tables)
        return all_tables
