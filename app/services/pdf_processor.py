"""
PDF Processing Service
Extracts text from uploaded PDF files using PyMuPDF (fitz) with automatic fallback to pypdf.
Supports both libraries so it works seamlessly on all Windows/Python environments.
"""
import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename

# Try importing PyMuPDF (fitz); if absent or compilation failed, use pure-Python pypdf
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class PDFProcessor:
    """Handles PDF validation, safe storage, and text extraction."""

    @staticmethod
    def allowed_file(filename, allowed_extensions={'pdf'}):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def save_file(file_storage, upload_folder):
        original_name = secure_filename(file_storage.filename)
        unique_prefix = uuid.uuid4().hex[:12]
        stored_filename = f"{unique_prefix}_{original_name}"
        save_path = Path(upload_folder) / stored_filename
        file_storage.save(save_path)
        return stored_filename, str(save_path)

    @classmethod
    def extract_text(cls, file_path):
        """
        Extracts readable text from PDF.
        Tries PyMuPDF first; falls back to pure-Python pypdf.
        Returns: (success: bool, text_or_error: str, page_count: int)
        """
        if HAS_FITZ:
            try:
                doc = fitz.open(file_path)
                page_count = len(doc)
                extracted_pages = []
                for page_num in range(page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text("text")
                    if text.strip():
                        extracted_pages.append(text.strip())
                doc.close()
                full_text = "\n\n".join(extracted_pages).strip()

                if not full_text or len(full_text.split()) < 10:
                    return (
                        False,
                        "This document contains little or no extractable digital text. "
                        "It may be a scanned image or photo PDF. "
                        "Optical Character Recognition (OCR) is not supported in ReadEase v1.0.",
                        page_count
                    )
                return True, full_text, page_count
            except Exception as e:
                pass  # Try pypdf fallback below

        if HAS_PYPDF:
            try:
                reader = pypdf.PdfReader(file_path)
                page_count = len(reader.pages)
                extracted_pages = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        extracted_pages.append(text.strip())
                full_text = "\n\n".join(extracted_pages).strip()

                if not full_text or len(full_text.split()) < 10:
                    return (
                        False,
                        "This document contains little or no extractable digital text. "
                        "It may be a scanned image or photo PDF. "
                        "Optical Character Recognition (OCR) is not supported in ReadEase v1.0.",
                        page_count
                    )
                return True, full_text, page_count
            except Exception as e:
                return False, f"An error occurred while reading the PDF: {str(e)}", 0

        return False, "No PDF extraction engine is installed. Please run: pip install pymupdf or pip install pypdf", 0
