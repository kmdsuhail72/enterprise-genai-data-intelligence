"""Document layout and reading-order analyzer."""

from dataclasses import dataclass
from typing import Any

from enterprise_ai.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContentBlock:
    """A classified structural block within a document page."""

    block_type: str  # text, header, table, image, footer, header_rule
    text: str
    bbox: tuple[float, float, float, float] | None = None
    confidence: float = 1.0


class LayoutAnalyzer:
    """Analyzes page blocks to determine reading order and distinguish narrative from tabular content."""

    @staticmethod
    def order_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort blocks in top-to-bottom, left-to-right reading order based on bounding boxes.

        Each block dict is expected to contain a 'bbox' tuple: (x0, y0, x1, y1).
        """

        def block_sort_key(block: dict[str, Any]) -> tuple[float, float]:
            bbox = block.get("bbox", (0, 0, 0, 0))
            # Quantize vertical coordinates into horizontal bands to handle multi-column or uneven baselines
            band = round(bbox[1] / 10.0) * 10.0
            return (band, bbox[0])

        return sorted(blocks, key=block_sort_key)

    @staticmethod
    def is_likely_scanned(char_count: int, page_area: float, image_count: int) -> bool:
        """Heuristic check to detect whether a page is primarily an image/scan needing OCR."""
        # If very few characters extracted natively but images are present
        if char_count < 50 and image_count > 0:
            return True
        return False
