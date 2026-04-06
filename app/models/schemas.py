"""Pydantic models for request/response validation."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# --- Document Types ---
class DocumentType(str, Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DiscrepancyType(str, Enum):
    AMOUNT_MISMATCH = "amount_mismatch"
    DATE_MISMATCH = "date_mismatch"
    COMPANY_MISMATCH = "company_mismatch"
    MISSING_FIELD = "missing_field"
    DUPLICATE_DOCUMENT = "duplicate_document"
    LOGICAL_ERROR = "logical_error"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# --- Extracted Data ---
class MoneyAmount(BaseModel):
    value: float
    currency: str = "USD"
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractedEntity(BaseModel):
    field: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class InvoiceData(BaseModel):
    invoice_number: str | None = None
    date: str | None = None
    due_date: str | None = None
    vendor_name: str | None = None
    vendor_address: str | None = None
    buyer_name: str | None = None
    buyer_address: str | None = None
    subtotal: MoneyAmount | None = None
    tax: MoneyAmount | None = None
    total: MoneyAmount | None = None
    line_items: list[dict] = []
    payment_terms: str | None = None


class ReceiptData(BaseModel):
    store_name: str | None = None
    store_address: str | None = None
    date: str | None = None
    time: str | None = None
    items: list[dict] = []
    subtotal: MoneyAmount | None = None
    tax: MoneyAmount | None = None
    total: MoneyAmount | None = None
    payment_method: str | None = None
    transaction_id: str | None = None


class ContractData(BaseModel):
    contract_number: str | None = None
    title: str | None = None
    parties: list[str] = []
    effective_date: str | None = None
    expiration_date: str | None = None
    total_value: MoneyAmount | None = None
    key_terms: list[str] = []
    obligations: list[str] = []
    termination_clause: str | None = None


# --- Classification ---
class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


# --- Extraction ---
class ExtractionResult(BaseModel):
    document_type: DocumentType
    raw_text: str
    extracted_data: InvoiceData | ReceiptData | ContractData | dict
    entities: list[ExtractedEntity] = []
    overall_confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel


# --- Validation / Discrepancies ---
class Discrepancy(BaseModel):
    type: DiscrepancyType
    severity: SeverityLevel
    description: str
    document_a: str
    document_b: str
    field: str
    value_a: str
    value_b: str
    suggestion: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    discrepancies: list[Discrepancy] = []
    summary: str
    documents_analyzed: int
    risk_score: float = Field(ge=0.0, le=1.0, description="0=no risk, 1=high risk")


# --- AI Summary ---
class DocumentSummary(BaseModel):
    document_id: str
    document_type: DocumentType
    summary: str
    key_findings: list[str] = []
    issues_found: list[str] = []
    risk_level: SeverityLevel


# --- Full Analysis ---
class FullAnalysisResult(BaseModel):
    document_id: str
    filename: str
    classification: ClassificationResult
    extraction: ExtractionResult
    summary: DocumentSummary
    processed_at: datetime = Field(default_factory=datetime.utcnow)


# --- API Responses ---
class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_configured: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
