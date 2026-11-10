"""Comprehensive unit tests for the document extraction engine."""

import io
import docx
import pymupdf as fitz
import pandas as pd
import pytest
from PIL import Image

from enterprise_ai.core.exceptions import UnsupportedFileTypeError
from enterprise_ai.extraction.csv_extractor import CSVExtractor
from enterprise_ai.extraction.docx_extractor import DocxExtractor
from enterprise_ai.extraction.excel_extractor import ExcelExtractor
from enterprise_ai.extraction.image_extractor import ImageExtractor
from enterprise_ai.extraction.pdf_extractor import PDFExtractor
from enterprise_ai.extraction.router import ExtractionRouter
from enterprise_ai.extraction.schemas import ExtractedDocument, ExtractedPage, ExtractedTable
from enterprise_ai.extraction.table_extractor import TableExtractor


class TestTableExtractor:
    """Tests for table extraction and markdown formatting."""

    def test_from_rows_markdown_formatting(self):
        headers = ["Department", "Q1 Revenue", "Q2 Revenue"]
        rows = [
            ["Cloud Services", "$12,500,000", "$15,200,000"],
            ["Enterprise Software", "$8,300,000", "$9,100,000"],
        ]
        table = TableExtractor.from_rows([headers] + rows, page_number=1, table_index=1)
        assert table is not None
        assert table.headers == headers
        assert len(table.rows) == 2
        md = table.to_markdown()
        assert "| Department | Q1 Revenue | Q2 Revenue |" in md
        assert "| Cloud Services | $12,500,000 | $15,200,000 |" in md

    def test_parse_markdown_table(self):
        text = """
        Here is the financial breakdown for the prior year:

        | Metric | 2022 | 2023 |
        | --- | --- | --- |
        | Gross Margin | 64.5% | 68.2% |
        | Operating Margin | 28.1% | 31.4% |

        Additional commentary follows below.
        """
        tables = TableExtractor.parse_markdown_table(text, page_number=1)
        assert len(tables) == 1
        tbl = tables[0]
        assert tbl.headers == ["Metric", "2022", "2023"]
        assert len(tbl.rows) == 2
        assert tbl.rows[0][0] == "Gross Margin"


class TestCSVExtractor:
    """Tests for CSV extraction with delimiter detection."""

    @pytest.mark.asyncio
    async def test_extract_comma_csv(self):
        csv_data = b"Quarter,Revenue,Cost,Profit\nQ1,1000,600,400\nQ2,1200,700,500\nQ3,1500,800,700\n"
        extractor = CSVExtractor()
        doc: ExtractedDocument = await extractor.extract(io.BytesIO(csv_data), "financial_summary.csv")

        assert doc.filename == "financial_summary.csv"
        assert doc.file_type == "csv"
        assert doc.total_pages == 1
        page = doc.pages[0]
        assert len(page.tables) == 1
        table = page.tables[0]
        assert table.headers == ["Quarter", "Revenue", "Cost", "Profit"]
        assert len(table.rows) == 3
        assert "financial_summary.csv" in page.cleaned_text

    @pytest.mark.asyncio
    async def test_extract_semicolon_csv(self):
        csv_data = "Item;Unit Price;Quantity\nWidget A;10.50;100\nWidget B;25.00;40\n".encode("utf-8")
        extractor = CSVExtractor()
        doc = await extractor.extract(io.BytesIO(csv_data), "inventory.csv")
        assert doc.total_pages == 1
        table = doc.pages[0].tables[0]
        assert table.headers == ["Item", "Unit Price", "Quantity"]
        assert len(table.rows) == 2


class TestPDFExtractor:
    """Tests for PyMuPDF PDF extraction."""

    @pytest.mark.asyncio
    async def test_extract_native_pdf(self):
        # Create a programmatic 2-page PDF
        pdf_doc = fitz.open()

        # Page 1
        p1 = pdf_doc.new_page()
        p1.insert_text((50, 72), "Enterprise GenAI Platform Architecture Overview\nConfidential Document.")

        # Page 2 with text
        p2 = pdf_doc.new_page()
        p2.insert_text((50, 72), "Financial Results\nQ4 Net Income reached $45.2M reflecting strong cloud adoption.")

        pdf_bytes = pdf_doc.tobytes()
        pdf_doc.close()

        extractor = PDFExtractor()
        doc = await extractor.extract(io.BytesIO(pdf_bytes), "architecture_brief.pdf")

        assert doc.filename == "architecture_brief.pdf"
        assert doc.file_type == "pdf"
        assert doc.total_pages == 2
        assert len(doc.pages) == 2
        assert "Enterprise GenAI Platform" in doc.pages[0].cleaned_text
        assert "Financial Results" in doc.pages[1].cleaned_text
        assert doc.pages[0].extraction_method == "native_pdf"


class TestDocxExtractor:
    """Tests for Word .docx extraction."""

    @pytest.mark.asyncio
    async def test_extract_docx(self):
        doc = docx.Document()
        doc.add_heading("Executive Summary", level=1)
        doc.add_paragraph("This document outlines the Q3 performance highlights.")

        # Add a table
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Metric"
        table.cell(0, 1).text = "Value"
        table.cell(1, 0).text = "ARR"
        table.cell(1, 1).text = "$120M"

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        extractor = DocxExtractor()
        extracted = await extractor.extract(buffer, "executive_summary.docx")

        assert extracted.filename == "executive_summary.docx"
        assert extracted.file_type == "docx"
        assert extracted.total_pages == 1
        page = extracted.pages[0]
        assert "# Executive Summary" in page.cleaned_text
        assert len(page.tables) == 1
        assert page.tables[0].headers == ["Metric", "Value"]
        assert page.tables[0].rows[0] == ["ARR", "$120M"]


class TestExcelExtractor:
    """Tests for Excel .xlsx extraction."""

    @pytest.mark.asyncio
    async def test_extract_excel(self):
        # Create Excel workbook with two sheets
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_income = pd.DataFrame({
                "Line_Item": ["Revenue", "COGS", "Gross Profit"],
                "Amount_2023": [1000, 400, 600],
            })
            df_income.to_excel(writer, sheet_name="Income_Statement", index=False)

            df_balance = pd.DataFrame({
                "Asset": ["Cash", "Receivables", "Equipment"],
                "Value": [250, 150, 500],
            })
            df_balance.to_excel(writer, sheet_name="Balance_Sheet", index=False)

        buffer.seek(0)
        extractor = ExcelExtractor()
        extracted = await extractor.extract(buffer, "financial_model.xlsx")

        assert extracted.filename == "financial_model.xlsx"
        assert extracted.file_type == "excel"
        assert extracted.total_pages == 2
        assert len(extracted.pages) == 2

        sheet1 = extracted.pages[0]
        assert sheet1.metadata["sheet_name"] == "Income_Statement"
        assert len(sheet1.tables) == 1
        assert sheet1.tables[0].headers == ["Line_Item", "Amount_2023"]

        sheet2 = extracted.pages[1]
        assert sheet2.metadata["sheet_name"] == "Balance_Sheet"
        assert sheet2.tables[0].headers == ["Asset", "Value"]


class TestImageExtractor:
    """Tests for standalone image extraction."""

    @pytest.mark.asyncio
    async def test_extract_image_metadata(self):
        # Create a simple synthetic test image
        img = Image.new("RGB", (300, 150), color=(255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        extractor = ImageExtractor()
        extracted = await extractor.extract(buffer, "diagram.png")

        assert extracted.filename == "diagram.png"
        assert extracted.file_type == "image"
        assert extracted.total_pages == 1
        assert extracted.pages[0].metadata["width"] == 300
        assert extracted.metadata["dimensions"] == "300x150"


class TestExtractionRouter:
    """Tests for router dispatch and extension validation."""

    def test_router_selects_correct_extractor(self):
        router = ExtractionRouter()
        assert router.get_extractor("report.pdf").__class__.__name__ == "PDFExtractor"
        assert router.get_extractor("memo.docx").__class__.__name__ == "DocxExtractor"
        assert router.get_extractor("model.xlsx").__class__.__name__ == "ExcelExtractor"
        assert router.get_extractor("data.csv").__class__.__name__ == "CSVExtractor"
        assert router.get_extractor("scan.png").__class__.__name__ == "ImageExtractor"

    def test_router_rejects_unsupported_extension(self):
        router = ExtractionRouter()
        with pytest.raises(UnsupportedFileTypeError):
            router.get_extractor("binary.exe")
