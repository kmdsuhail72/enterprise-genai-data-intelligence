"""OCR processing engine with multi-backend support and graceful fallback."""

import io
from typing import Any
from PIL import Image

from enterprise_ai.core.exceptions import OCRError
from enterprise_ai.core.logging import get_logger

logger = get_logger(__name__)


class OCREngine:
    """Coordinates OCR processing for scanned pages and images."""

    def __init__(self, lang: str = "en", use_angle_cls: bool = True):
        self.lang = lang
        self.use_angle_cls = use_angle_cls
        self._paddle_ocr: Any = None
        self._ocr_available: bool | None = None

    @property
    def is_available(self) -> bool:
        """Check if an OCR engine (PaddleOCR, Tesseract) is installed and operational."""
        if self._ocr_available is None:
            try:
                import paddleocr  # noqa: F401

                self._ocr_available = True
            except ImportError:
                try:
                    import pytesseract  # noqa: F401

                    self._ocr_available = True
                except ImportError:
                    self._ocr_available = False
        return self._ocr_available

    def _get_paddle_instance(self) -> Any:
        if self._paddle_ocr is None:
            from paddleocr import PaddleOCR

            self._paddle_ocr = PaddleOCR(
                use_angle_cls=self.use_angle_cls,
                lang=self.lang,
                show_log=False,
            )
        return self._paddle_ocr

    async def ocr_image(self, image_bytes: bytes) -> tuple[str, list[dict[str, Any]]]:
        """Perform OCR on image bytes.

        Returns
        -------
        tuple[str, list[dict]]
            Extracted text string and list of bounding box annotations.
        """
        if not self.is_available:
            logger.warning("ocr_engine_not_available_skipping")
            return "", []

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # 1. Try PaddleOCR
            try:
                from paddleocr import PaddleOCR

                engine = self._get_paddle_instance()
                result = engine.ocr(image_bytes, cls=self.use_angle_cls)
                lines = []
                boxes = []
                if result and result[0]:
                    for line in result[0]:
                        bbox = line[0]
                        text, conf = line[1]
                        lines.append(text)
                        boxes.append({"text": text, "confidence": conf, "bbox": bbox})
                return "\n".join(lines), boxes
            except ImportError:
                pass

            # 2. Try pytesseract fallback
            try:
                import pytesseract

                text = pytesseract.image_to_string(image, lang=self.lang)
                return text.strip(), []
            except ImportError:
                pass

            return "", []

        except Exception as exc:
            logger.error("ocr_processing_failed", error=str(exc))
            raise OCRError(f"OCR execution failed: {exc}")
