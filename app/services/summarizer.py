"""AI document summarization service."""
import json
import logging

import httpx

from app.config import settings
from app.models.schemas import DocumentSummary, DocumentType, SeverityLevel

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """You are a document analysis expert. Provide a concise summary of this {doc_type} document.

Document text:
```
{text}
```

Return ONLY valid JSON:
{{
  "summary": "2-3 sentence summary of the document",
  "key_findings": ["finding 1", "finding 2"],
  "issues_found": ["issue 1 if any"],
  "risk_level": "info|warning|critical"
}}"""


async def summarize_document(
    text: str,
    doc_type: DocumentType,
    document_id: str,
) -> DocumentSummary:
    """Generate AI summary of a document."""
    if not settings.OPENAI_API_KEY:
        return DocumentSummary(
            document_id=document_id,
            document_type=doc_type,
            summary="LLM not configured — unable to generate summary.",
            risk_level=SeverityLevel.INFO,
        )

    truncated = text[:6000]
    prompt = SUMMARY_PROMPT.format(doc_type=doc_type.value, text=truncated)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = json.loads(data["choices"][0]["message"]["content"])

        return DocumentSummary(
            document_id=document_id,
            document_type=doc_type,
            summary=content.get("summary", ""),
            key_findings=content.get("key_findings", []),
            issues_found=content.get("issues_found", []),
            risk_level=content.get("risk_level", "info"),
        )

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return DocumentSummary(
            document_id=document_id,
            document_type=doc_type,
            summary=f"Summary generation failed: {str(e)}",
            risk_level=SeverityLevel.INFO,
        )
