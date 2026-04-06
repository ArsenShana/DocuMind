# DocuMind AI

**Intelligent Document Analysis and Validation System**

DocuMind AI is a full-stack application that automates document processing for invoices, receipts, and contracts. It leverages LLM-powered classification, structured data extraction with confidence scoring, hybrid cross-document validation, and AI-generated summaries -- all accessible through a REST API and a modern React dashboard.

---

## Key Features

- **Smart Classification** -- automatically identifies document type (invoice, receipt, contract) with confidence scores and reasoning.
- **Structured Data Extraction** -- pulls dates, amounts, parties, line items, payment terms, and more into typed JSON with per-field confidence (0--1).
- **OCR Support** -- handles scanned PDFs and images via Tesseract OCR with automatic EXIF orientation correction.
- **Cross-Document Validation** -- hybrid engine combining deterministic rule-based checks with LLM semantic analysis to detect discrepancies across documents.
- **AI Summaries** -- generates concise overviews with key findings, issues found, and risk-level assessment.
- **Confidence Scoring** -- every extracted value and classification carries a 0--1 confidence score so you know what to trust.
- **Strictly Typed Output** -- all API responses are validated through 20+ Pydantic schemas, ready for downstream integration.

---

## Architecture

```
                         +------------------+
                         |   React Frontend |
                         |  (Vite + Nginx)  |
                         +--------+---------+
                                  |
                            /api  | proxy
                                  v
                         +------------------+
                         |  FastAPI Backend  |
                         |   (Uvicorn)      |
                         +--------+---------+
                                  |
          +-----------+-----------+-----------+-----------+
          |           |           |           |           |
          v           v           v           v           v
     +--------+  +--------+  +--------+  +--------+  +--------+
     | Parser |  |Classify|  |Extract |  |Summarize| |Validate|
     |--------|  |--------|  |--------|  |---------|  |--------|
     |PyMuPDF |  | OpenAI |  | OpenAI |  | OpenAI  |  |Rules + |
     |Tesseract| |  LLM   |  |  LLM   |  |  LLM    |  |  LLM   |
     +--------+  +--------+  +--------+  +---------+  +--------+

     PDF/Image      invoice     dates,       summary,     amount
     to text      receipt     amounts,    key findings   mismatch,
                  contract    parties      risk level    date gaps
```

### Processing Pipeline

```
Upload (PDF / PNG / JPG)
        |
        v
  [Document Parser]   PyMuPDF extracts embedded text; Tesseract OCR for scans
        |
        v
  [LLM Classifier]    GPT identifies: invoice / receipt / contract / unknown
        |
        v
  [Data Extractor]     Structured JSON with typed fields and confidence scores
        |
        v
  [AI Summarizer]      2-3 sentence summary, key findings, issues, risk level
        |
        v
  [Validation Engine]  Deterministic rules + LLM semantic checks (hybrid)
        |
        v
  Structured Results   Discrepancies, risk score, actionable suggestions
```

---

## Tech Stack

| Layer           | Technology                                  |
|-----------------|---------------------------------------------|
| Backend         | Python 3.12, FastAPI 0.115, Uvicorn         |
| LLM             | OpenAI API (GPT-4o-mini by default)         |
| PDF Parsing     | PyMuPDF 1.25                                |
| OCR             | Tesseract (eng + rus) via pytesseract       |
| Image Handling  | Pillow 11                                   |
| HTTP Client     | httpx 0.28 (async)                          |
| Validation      | Pydantic v2, pydantic-settings              |
| Frontend        | React 18, React Router 6, Vite 6            |
| UI Animations   | Framer Motion 11                            |
| Icons           | Lucide React                                |
| Reverse Proxy   | Nginx (serves SPA, proxies /api to backend) |
| Containerization| Docker, Docker Compose                      |

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An OpenAI API key

### Run with Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/ArsenShana/DocuMind.git
cd DocuMind

# 2. Configure environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# 3. Build and start
docker compose up -d --build

# 4. Open the application
#    Frontend:  http://localhost:8002
#    API docs:  http://localhost:8002/docs
#    Health:    http://localhost:8002/health
```

### Run Locally (without Docker)

```bash
# Backend
pip install -r requirements.txt
export OPENAI_API_KEY="your-key-here"
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Method | Endpoint                           | Description                                    |
|--------|------------------------------------|------------------------------------------------|
| `GET`  | `/`                                | Service info and available endpoints            |
| `GET`  | `/health`                          | Health check (status, version, LLM configured)  |
| `POST` | `/api/documents/upload`            | Upload a document (PDF, PNG, JPG, TIFF, BMP, WebP) |
| `POST` | `/api/documents/analyze/{id}`      | Full pipeline: parse, classify, extract, summarize |
| `POST` | `/api/documents/classify/{id}`     | Classify document type only                     |
| `POST` | `/api/documents/extract/{id}`      | Extract structured data only                    |
| `POST` | `/api/documents/validate`          | Cross-validate 2+ documents for discrepancies   |
| `GET`  | `/api/documents/`                  | List all uploaded documents                     |
| `GET`  | `/api/documents/{id}`              | Get document details and analysis results       |

---

## Usage Examples

### Upload and Analyze a Document

```bash
# Upload
curl -X POST http://localhost:8002/api/documents/upload \
  -F "file=@invoice.pdf"

# Response:
# {
#   "document_id": "a1b2c3d4e5f6",
#   "filename": "invoice.pdf",
#   "file_size": 54321,
#   "message": "Document uploaded successfully. Use /analyze/{document_id} to process."
# }

# Full analysis (classify + extract + summarize)
curl -X POST http://localhost:8002/api/documents/analyze/a1b2c3d4e5f6
```

### Classify Only

```bash
curl -X POST http://localhost:8002/api/documents/classify/a1b2c3d4e5f6

# Response:
# {
#   "document_type": "invoice",
#   "confidence": 0.95,
#   "reasoning": "Contains vendor info, line items, totals, and payment terms."
# }
```

### Extract Structured Data

```bash
curl -X POST http://localhost:8002/api/documents/extract/a1b2c3d4e5f6

# Response includes typed fields such as:
# {
#   "document_type": "invoice",
#   "extracted_data": {
#     "invoice_number": "INV-2026-0042",
#     "vendor_name": "Acme Corp",
#     "total": {"value": 1250.00, "currency": "USD", "confidence": 0.95},
#     "line_items": [...]
#   },
#   "overall_confidence": 0.92,
#   "confidence_level": "high"
# }
```

### Cross-Validate Documents

```bash
# Requires 2+ previously analyzed documents
curl -X POST http://localhost:8002/api/documents/validate \
  -H "Content-Type: application/json" \
  -d '["a1b2c3d4e5f6", "f6e5d4c3b2a1"]'

# Response:
# {
#   "is_valid": false,
#   "discrepancies": [
#     {
#       "type": "amount_mismatch",
#       "severity": "critical",
#       "description": "Total amounts differ: $1250.00 vs $1350.00",
#       "field": "total",
#       "suggestion": "Verify which amount is correct and check for calculation errors."
#     }
#   ],
#   "risk_score": 0.3,
#   "documents_analyzed": 2
# }
```

### Check Service Health

```bash
curl http://localhost:8002/health

# {"status": "ok", "version": "1.0.0", "llm_configured": true}
```

---

## How Cross-Validation Works

The validation engine uses a **hybrid approach** that combines deterministic rules with LLM intelligence.

### Step 1: Rule-Based Checks (Deterministic)

Fast, reliable checks that run without LLM calls:

| Check                    | Logic                                                        | Severity  |
|--------------------------|--------------------------------------------------------------|-----------|
| Amount mismatch          | Compares total amounts across documents (tolerance: $0.01)   | Critical if >10% difference, else Warning |
| Date mismatch            | Checks date consistency across related documents             | Warning   |
| Company name mismatch    | Case-insensitive comparison of vendor/store/party names      | Warning   |
| Math verification        | Validates subtotal + tax = total within each document        | Critical  |

### Step 2: LLM-Based Analysis (Semantic)

The LLM acts as a forensic document analyst, looking for:

- Logical inconsistencies that rules cannot catch
- Potential duplicate documents
- Missing required fields
- Cross-reference errors
- Overall risk assessment

### Step 3: Merge and Deduplicate

Results from both engines are merged and deduplicated by `(type, field, document_a, document_b)`. A composite risk score is calculated:

```
risk_score = min(1.0, critical_count * 0.3 + warning_count * 0.1 + llm_risk * 0.3)
```

A document set is marked **invalid** if any critical-severity discrepancy is found.

---

## Frontend

The React frontend provides a modern single-page application with three main views:

### Landing Page
- Hero section with animated gradients
- Feature overview (classification, extraction, validation, summaries, confidence scoring, structured output)
- Step-by-step pipeline visualization
- Call-to-action linking to the dashboard

### Dashboard -- Upload and Analyze
- Drag-and-drop file upload (PDF, PNG, JPG up to 20 MB)
- Real-time progress indicators for upload and analysis stages
- Results displayed as cards: classification with confidence bar, extracted data grid with line-item tables, and AI summary with key findings and issues

### Dashboard -- Cross-Validation
- Select 2+ previously analyzed documents from a list
- Run validation and view discrepancies as severity-tagged cards (critical / warning / info)
- Risk score meter and overall summary

### Dashboard -- Documents
- List of all uploaded documents with their analysis status (Analyzed / Pending)

The frontend is built with Vite and served via Nginx, which also reverse-proxies `/api` requests to the FastAPI backend.

---

## Project Structure

```
DocuMindAI/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, CORS, routers
│   ├── config.py                # Settings (env vars, defaults)
│   ├── api/
│   │   ├── __init__.py
│   │   └── documents.py         # REST endpoints (upload, analyze, validate)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # 20+ Pydantic models (request/response)
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── document_parser.py   # PDF text extraction, OCR, metadata
│   └── services/
│       ├── __init__.py
│       ├── classifier.py        # LLM document type classification
│       ├── extractor.py         # LLM structured data extraction
│       ├── summarizer.py        # LLM summary generation
│       └── validator.py         # Hybrid validation engine (rules + LLM)
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # React entry point
│   │   ├── App.jsx              # Router setup
│   │   ├── api.js               # Backend API client
│   │   ├── index.css            # Global styles
│   │   ├── components/
│   │   │   └── Navbar.jsx       # Navigation bar
│   │   └── pages/
│   │       ├── Landing.jsx      # Landing page with features
│   │       └── Dashboard.jsx    # Upload, validate, documents views
│   ├── Dockerfile               # Multi-stage: Node build + Nginx
│   ├── nginx.conf               # Reverse proxy config
│   ├── package.json             # React, Framer Motion, Lucide
│   ├── vite.config.js           # Vite configuration
│   └── index.html               # HTML entry point
├── samples/                     # Sample test documents
│   ├── invoice_sample.pdf
│   ├── receipt_sample.pdf
│   ├── receipt_mismatched.pdf
│   ├── contract_sample.pdf
│   └── test_image_invoice.png
├── tests/
│   └── create_samples.py        # Script to generate test PDFs
├── Dockerfile                   # Python 3.12 + Tesseract OCR
├── docker-compose.yml           # Backend + Frontend services
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── .gitignore
```

---

## Configuration

All settings are managed via environment variables (or a `.env` file):

| Variable             | Default         | Description                                      |
|----------------------|-----------------|--------------------------------------------------|
| `OPENAI_API_KEY`     | *(required)*    | OpenAI API key for LLM features                  |
| `OPENAI_MODEL`       | `gpt-4o-mini`   | OpenAI model to use for all LLM calls            |
| `OPENAI_TEMPERATURE` | `0.1`           | LLM temperature (lower = more deterministic)     |
| `UPLOAD_DIR`         | `./uploads`     | Directory for uploaded files                     |
| `MAX_FILE_SIZE_MB`   | `20`            | Maximum upload file size in megabytes            |
| `FAISS_INDEX_PATH`   | `./data/faiss_index` | Path for FAISS vector index storage         |
| `DEBUG`              | `false`         | Enable debug mode                                |

### Supported File Types

PDF, PNG, JPG, JPEG, TIFF, BMP, WebP

---

## License

MIT
