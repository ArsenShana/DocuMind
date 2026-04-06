"""Document classification service using LLM."""
import json
import logging

import httpx

from app.config import settings
from app.models.schemas import ClassificationResult, DocumentType

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are a document classification expert. Analyze the following document text and classify it into one of these categories:

1. **invoice** — A bill or invoice requesting payment for goods/services. Contains vendor info, line items, totals, payment terms.
2. **receipt** — A proof of payment/purchase. Contains store name, items purchased, amounts, payment method.
3. **contract** — A legal agreement between parties. Contains terms, obligations, dates, signatures.
4. **unknown** — If the document doesn't clearly fit any category.

Document text:
```
{text}
```

Respond with ONLY valid JSON in this exact format:
{{
  "document_type": "invoice|receipt|contract|unknown",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why this classification was chosen"
}}"""


async def classify_document(text: str) -> ClassificationResult:
    """Classify a document using LLM."""
    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI API key not set, returning unknown classification")
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            reasoning="LLM not configured — API key missing",
        )

    # Truncate to avoid token limits
    truncated = text[:6000]
    prompt = CLASSIFICATION_PROMPT.format(text=truncated)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": settings.OPENAI_TEMPERATURE,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = json.loads(data["choices"][0]["message"]["content"])

            return ClassificationResult(
                document_type=content.get("document_type", "unknown"),
                confidence=content.get("confidence", 0.5),
                reasoning=content.get("reasoning", ""),
            )

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            reasoning=f"Classification error: {str(e)}",
        )
