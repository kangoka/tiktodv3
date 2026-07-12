"""In-memory CAPTCHA readiness checks and OCR."""

import hashlib
import re
from io import BytesIO

import pytesseract
from PIL import Image


class CaptchaNotReadyError(RuntimeError):
    """Raised when OCR sees a loading or placeholder image."""


class CaptchaSolver:
    """Tesseract-backed CAPTCHA OCR with no persistent image files."""

    _PLACEHOLDER_RE = re.compile(r"\b(?:loading|please\s+wait|wait)\b", re.IGNORECASE)
    _MIN_TEXT_LENGTH = 3
    _MAX_TEXT_LENGTH = 10

    @staticmethod
    def ensure_available():
        try:
            pytesseract.get_tesseract_version()
        except Exception as exc:  # pytesseract exposes platform-specific errors
            raise RuntimeError(
                "Tesseract OCR is unavailable. Install Tesseract and add it to PATH, "
                "then retry Setup."
            ) from exc

    @staticmethod
    def fingerprint(image_bytes):
        """Return a stable digest of decoded pixels, not PNG metadata."""
        with Image.open(BytesIO(image_bytes)) as image:
            normalized = image.convert("L")
            payload = (
                f"{normalized.width}x{normalized.height}:".encode()
                + normalized.tobytes()
            )
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def normalize_text(cls, text):
        return re.sub(r"[^A-Za-z0-9]", "", text)

    @classmethod
    def solve(cls, image_bytes):
        with Image.open(BytesIO(image_bytes)) as image:
            raw_text = pytesseract.image_to_string(
                image, config=r"--oem 3 --psm 6"
            ).strip()

        if cls._PLACEHOLDER_RE.search(raw_text):
            raise CaptchaNotReadyError("Captcha image is still loading")

        captcha_text = cls.normalize_text(raw_text)
        if not cls._MIN_TEXT_LENGTH <= len(captcha_text) <= cls._MAX_TEXT_LENGTH:
            raise RuntimeError(
                "OCR did not return a valid 3-10 character captcha value"
            )
        return captcha_text
