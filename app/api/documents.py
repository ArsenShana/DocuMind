"""Document analysis API endpoints."""
import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.models.schemas import (
    UploadResponse, FullAnalysisResult, ClassificationResult,
    ExtractionResult, ValidationResult, DocumentSummary, ErrorResponse,
)
from app.parsers.document_parser import parse_document, get_document_metadata
from app.services.classifier import classify_document
from app.services.extractor import extract_data
from app.services.summarizer import summarize_document
from app.services.validator import validate_documents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# In-memory store for processed documents (use DB in production)
_document_store: dict[str, dict] = {}


def _save_file(file: UploadFile) -> tuple[str, str]:
    """Save uploaded file and return (document_id, file_path)."""
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {settings.ALLOWED_EXTENSIONS}")

    doc_id = uuid.uuid4().hex[:12]
    safe_name = f"{doc_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    content = file.file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB")

    with open(file_path, "wb") as f:
        f.write(content)

    return doc_id, file_path


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for processing."""
    doc_id, file_path = _save_file(file)
    metadata = get_document_metadata(file_path)

    _document_store[doc_id] = {
        "file_path": file_path,
        "filename": file.filename,
        "metadata": metadata,
    }

    return UploadResponse(
        document_id=doc_id,
        filename=file.filename,
        file_size=metadata["size_bytes"],
        message="Document uploaded successfully. Use /analyze/{document_id} to process.",
    )


@router.post("/analyze/{document_id}", response_model=FullAnalysisResult)
async def analyze_document(document_id: str):
    """Run full analysis pipeline: parse → classify → extract → summarize."""
    doc = _document_store.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found. Upload first via /upload.")

    # Step 1: Parse text
    try:
        text = parse_document(doc["file_path"])
    except Exception as e:
        raise HTTPException(422, f"Failed to parse document: {e}")

    if not text.strip():
        raise HTTPException(422, "No text could be extracted from the document.")

    # Step 2: Classify
    classification = await classify_document(text)

    # Step 3: Extract structured data
    extraction = await extract_data(text, classification.document_type)

    # Step 4: Summarize
    summary = await summarize_document(text, classification.document_type, document_id)

    # Store results
    doc["text"] = text
    doc["classification"] = classification
    doc["extraction"] = extraction
    doc["summary"] = summary

    return FullAnalysisResult(
        document_id=document_id,
        filename=doc["filename"],
        classification=classification,
        extraction=extraction,
        summary=summary,
    )


@router.post("/classify/{document_id}", response_model=ClassificationResult)
async def classify_only(document_id: str):
    """Classify document type only."""
    doc = _document_store.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")

    text = doc.get("text") or parse_document(doc["file_path"])
    doc["text"] = text
    result = await classify_document(text)
    doc["classification"] = result
    return result


@router.post("/extract/{document_id}", response_model=ExtractionResult)
async def extract_only(document_id: str):
    """Extract structured data from document."""
    doc = _document_store.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")

    text = doc.get("text") or parse_document(doc["file_path"])
    doc["text"] = text

    classification = doc.get("classification") or await classify_document(text)
    doc["classification"] = classification

    result = await extract_data(text, classification.document_type)
    doc["extraction"] = result
    return result


@router.post("/validate", response_model=ValidationResult)
async def validate_cross_documents(document_ids: list[str]):
    """Cross-validate multiple documents for discrepancies.

    Requires at least 2 previously uploaded and analyzed documents.
    """
    if len(document_ids) < 2:
        raise HTTPException(400, "At least 2 document IDs required for cross-validation.")

    documents = []
    for doc_id in document_ids:
        doc = _document_store.get(doc_id)
        if not doc:
            raise HTTPException(404, f"Document {doc_id} not found.")

        text = doc.get("text")
        extraction = doc.get("extraction")

        if not text or not extraction:
            raise HTTPException(400, f"Document {doc_id} has not been analyzed yet. Run /analyze/{doc_id} first.")

        documents.append((doc_id, text, extraction))

    return await validate_documents(documents)


@router.get("/{document_id}")
async def get_document_info(document_id: str):
    """Get stored information about a processed document."""
    doc = _document_store.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")

    result = {
        "document_id": document_id,
        "filename": doc["filename"],
        "metadata": doc["metadata"],
    }

    if doc.get("classification"):
        result["classification"] = doc["classification"]
    if doc.get("summary"):
        result["summary"] = doc["summary"]

    return result


@router.get("/")
async def list_documents():
    """List all uploaded documents."""
    return [
        {
            "document_id": doc_id,
            "filename": doc["filename"],
            "analyzed": "extraction" in doc,
        }
        for doc_id, doc in _document_store.items()
    ]
