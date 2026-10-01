"""
OCR text extraction using EasyOCR. The reader is expensive to initialize
(it loads a detection + recognition model), so it's created once lazily
and reused for the lifetime of the process.

PDFs are rasterized to images with PyMuPDF first, since EasyOCR itself
only reads images. Only the first page is processed — receipts and bills
are virtually always single-page; this keeps processing fast and
predictable.
"""
import io
import logging

logger = logging.getLogger("expense_manager")

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr

        logger.info("Loading EasyOCR model (first use in this process)...")
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader


def _pdf_first_page_to_png_bytes(pdf_bytes: bytes) -> bytes:
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.page_count == 0:
            raise ValueError("PDF has no pages.")
        page = doc.load_page(0)
        # Render at 2x zoom for sharper text before OCR.
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        return pixmap.tobytes("png")
    finally:
        doc.close()


def extract_text(file_bytes: bytes, file_extension: str) -> str:
    """
    Extracts text from an uploaded receipt/bill.

    file_extension: the lowercase extension including the dot, e.g. ".png", ".pdf".
    Raises on failure — callers are expected to catch this and mark the
    document's processing_status as "failed" rather than losing the upload.
    """
    ext = file_extension.lower()

    if ext == ".pdf":
        image_bytes = _pdf_first_page_to_png_bytes(file_bytes)
    elif ext in (".jpg", ".jpeg", ".png"):
        image_bytes = file_bytes
    else:
        raise ValueError(f"Unsupported file type for OCR: {ext}")

    reader = _get_reader()
    lines = reader.readtext(io.BytesIO(image_bytes).getvalue(), detail=0)
    return "\n".join(lines).strip()
