"""
Business logic for receipt/bill uploads: validation, storage, and OCR
text extraction. Kept separate from the router so each step is testable
and the OCR/storage backends stay swappable.
"""
import logging
import os

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.services import ocr_service
from app.services.storage_service import get_storage_service

logger = logging.getLogger("expense_manager")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


class DocumentValidationError(Exception):
    """Raised for expected validation failures (bad type, too large, etc.)."""


class DocumentNotFoundError(Exception):
    """Raised when a document doesn't exist or doesn't belong to the user."""


def validate_upload(filename: str, file_bytes: bytes) -> str:
    """Validates file type and size. Returns the lowercase extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentValidationError(
            f"Unsupported file type '{ext}'. Allowed types: JPG, JPEG, PNG, PDF."
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise DocumentValidationError(
            f"File is too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if len(file_bytes) == 0:
        raise DocumentValidationError("The uploaded file is empty.")

    return ext


def process_upload(db: Session, user_id: int, filename: str, file_bytes: bytes) -> Document:
    """
    Validates, stores, and OCR-processes an uploaded receipt/bill.
    The document is always saved — even if OCR fails, so the user doesn't
    lose their upload — with processing_status reflecting the outcome.
    """
    ext = validate_upload(filename, file_bytes)

    storage = get_storage_service()
    file_url = storage.save(file_bytes, filename, user_id)

    document = Document(
        user_id=user_id,
        filename=filename,
        file_url=file_url,
        file_type=ext.lstrip("."),
        ocr_text=None,
        processing_status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        extracted_text = ocr_service.extract_text(file_bytes, ext)
        document.ocr_text = extracted_text
        document.processing_status = "completed"
    except Exception:
        logger.exception(f"OCR failed for document {document.id}")
        document.processing_status = "failed"

    db.commit()
    db.refresh(document)
    return document


def list_documents(db: Session, user_id: int) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


def get_document(db: Session, user_id: int, document_id: int) -> Document:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )
    if not document:
        raise DocumentNotFoundError("Document not found.")
    return document


def delete_document(db: Session, user_id: int, document_id: int) -> None:
    document = get_document(db, user_id, document_id)
    db.delete(document)
    db.commit()
