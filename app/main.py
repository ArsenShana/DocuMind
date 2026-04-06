"""DocuMind AI — Intelligent Document Analysis & Validation System."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.documents import router as documents_router
from app.models.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocuMind AI",
    description=(
        "Intelligent document analysis and validation system powered by LLM. "
        "Classifies documents (invoice, receipt, contract), extracts structured data "
        "with confidence scores, performs cross-document validation, and generates AI summaries."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "upload": "POST /api/documents/upload",
            "analyze": "POST /api/documents/analyze/{document_id}",
            "classify": "POST /api/documents/classify/{document_id}",
            "extract": "POST /api/documents/extract/{document_id}",
            "validate": "POST /api/documents/validate",
            "list": "GET /api/documents/",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["root"])
async def health():
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        llm_configured=bool(settings.OPENAI_API_KEY),
    )
