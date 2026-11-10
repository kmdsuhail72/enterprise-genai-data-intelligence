"""Table extraction and structural normalization utility."""

import json
from typing import Any
import pandas as pd

from enterprise_ai.core.logging import get_logger
from enterprise_ai.extraction.schemas import ExtractedTable

logger = get_logger(__name__)


class TableExtractor:
    """Detects, normalizes, and extracts tabular structures from text or cell grids."""

    @staticmethod
    def from_rows(
        rows: list[list[Any]],
        page_number: int,
        table_index: int = 1,
        title: str | None = None,
        sheet_name: str | None = None,
    ) -> ExtractedTable | None:
        """Construct an ExtractedTable from a 2D matrix of cell values."""
        if not rows or not any(rows):
            return None

        # Filter empty rows
        cleaned_rows = []
        for row in rows:
            if any(cell is not None and str(cell).strip() != "" for cell in row):
                cleaned_rows.append([str(c).strip() if c is not None else "" for c in row])

        if not cleaned_rows:
            return None

        # Determine header vs data
        headers = cleaned_rows[0]
        data_rows = cleaned_rows[1:] if len(cleaned_rows) > 1 else []

        # Convert to pandas DataFrame for JSON serialization
        try:
            df = pd.DataFrame(data_rows, columns=headers) if data_rows else pd.DataFrame(columns=headers)
            df_json = df.to_json(orient="split")
        except Exception:
            df_json = json.dumps({"headers": headers, "rows": data_rows})

        return ExtractedTable(
            table_index=table_index,
            page_number=page_number,
            headers=headers,
            rows=data_rows,
            title=title,
            sheet_name=sheet_name,
            dataframe_json=df_json,
        )

    @staticmethod
    def parse_markdown_table(
        text: str,
        page_number: int,
        start_index: int = 1,
    ) -> list[ExtractedTable]:
        """Scan text for markdown-formatted tables and parse them."""
        tables: list[ExtractedTable] = []
        lines = text.splitlines()
        current_table_lines: list[str] = []
        in_table = False
        tbl_idx = start_index

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                current_table_lines.append(stripped)
            else:
                if in_table and len(current_table_lines) >= 2:
                    # Parse accumulated table lines
                    matrix = []
                    for t_line in current_table_lines:
                        # Skip markdown separator line |---|---|
                        test_sep = t_line.replace("|", "").replace(" ", "").replace("-", "").replace(":", "")
                        if not test_sep:
                            continue
                        cells = [c.strip() for c in t_line.strip("|").split("|")]
                        matrix.append(cells)

                    if matrix:
                        tbl = TableExtractor.from_rows(matrix, page_number=page_number, table_index=tbl_idx)
                        if tbl:
                            tables.append(tbl)
                            tbl_idx += 1
                in_table = False
                current_table_lines = []

        # Handle table at EOF
        if in_table and len(current_table_lines) >= 2:
            matrix = []
            for t_line in current_table_lines:
                test_sep = t_line.replace("|", "").replace(" ", "").replace("-", "").replace(":", "")
                if not test_sep:
                    continue
                cells = [c.strip() for c in t_line.strip("|").split("|")]
                matrix.append(cells)
            if matrix:
                tbl = TableExtractor.from_rows(matrix, page_number=page_number, table_index=tbl_idx)
                if tbl:
                    tables.append(tbl)

        return tables
