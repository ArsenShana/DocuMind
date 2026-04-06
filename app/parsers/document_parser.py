"""Document parser — extracts text from PDF and image files.

Uses PyMuPDF for PDFs and Tesseract OCR for images (photos, scans).
"""
import os
import logging
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF.

    If a page has no embedded text (scanned PDF), falls back to OCR.
    """
    try:
        doc = fitz.open(file_path)
        pages = []

        for page_num, page in enumerate(doc):
            text = page.get_text("text")

            # If no embedded text — page is likely a scan, use OCR
            if not text.strip():
                logger.info(f"Page {page_num + 1} has no text, running OCR...")
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img, lang="eng+rus")

            if text.strip():
                pages.append(f"--- Page {page_num + 1} ---\n{text}")

        doc.close()

        if not pages:
            logger.warning(f"No text extracted from PDF: {file_path}")
            return ""

        full_text = "\n\n".join(pages)
        logger.info(f"Extracted {len(full_text)} chars from {len(pages)} pages: {file_path}")
        return full_text

    except Exception as e:
        logger.error(f"PDF extraction failed for {file_path}: {e}")
        raise ValueError(f"Failed to parse PDF: {e}")


def extract_text_from_image(file_path: str) -> str:
    """Extract text from image using Tesseract OCR."""
    try:
        img = Image.open(file_path)

        # Auto-detect orientation and apply EXIF rotation
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        text = pytesseract.image_to_string(img, lang="eng+rus")

        if not text.strip():
            logger.warning(f"No text extracted from image: {file_path}")
            return ""

        logger.info(f"OCR extracted {len(text)} chars from image: {file_path}")
        return text

    except Exception as e:
        logger.error(f"Image OCR failed for {file_path}: {e}")
        raise ValueError(f"Failed to OCR image: {e}")


def parse_document(file_path: str) -> str:
    """Parse a document and return extracted text. Supports PDF and images."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"):
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def get_document_metadata(file_path: str) -> dict:
    """Get basic metadata about a document."""
    path = Path(file_path)
    stat = path.stat()

    metadata = {
        "filename": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
    }

    if path.suffix.lower() == ".pdf":
        try:
            doc = fitz.open(file_path)
            metadata["pages"] = len(doc)
            metadata["pdf_metadata"] = dict(doc.metadata) if doc.metadata else {}
            doc.close()
        except Exception:
            pass
    elif path.suffix.lower() in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"):
        try:
            img = Image.open(file_path)
            metadata["image_size"] = f"{img.width}x{img.height}"
            metadata["image_mode"] = img.mode
        except Exception:
            pass

    return metadata
