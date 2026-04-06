"""Structured data extraction service using LLM."""
import json
import logging

import httpx

from app.config import settings
from app.models.schemas import (
    DocumentType, ExtractionResult, ExtractedEntity,
    InvoiceData, ReceiptData, ContractData, MoneyAmount, ConfidenceLevel,
)

logger = logging.getLogger(__name__)

INVOICE_EXTRACTION_PROMPT = """You are a financial document expert. Extract structured data from this invoice text.

Document text:
```
{text}
```

Return ONLY valid JSON:
{{
  "invoice_number": "string or null",
  "date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "buyer_name": "string or null",
  "buyer_address": "string or null",
  "subtotal": {{"value": 0.00, "currency": "USD", "confidence": 0.9}},
  "tax": {{"value": 0.00, "currency": "USD", "confidence": 0.9}},
  "total": {{"value": 0.00, "currency": "USD", "confidence": 0.9}},
  "line_items": [{{"description": "item", "quantity": 1, "unit_price": 0.00, "amount": 0.00}}],
  "payment_terms": "string or null",
  "entities": [{{"field": "field_name", "value": "extracted_value", "confidence": 0.9}}],
  "overall_confidence": 0.85
}}"""

RECEIPT_EXTRACTION_PROMPT = """You are a financial document expert. Extract structured data from this receipt text.

Document text:
```
{text}
```

Return ONLY valid JSON:
{{
  "store_name": "string or null",
  "store_address": "string or null",
  "date": "YYYY-MM-DD or null",
  "time": "HH:MM or null",
  "items": [{{"name": "item", "quantity": 1, "price": 0.00}}],
  "subtotal": {{"value": 0.00, "currency": "USD", "confidence": 0.9}},
  "tax": {{"value": 0.00, "currency": "USD", "confidence": 0.9}},
  "total": {{"value": 0.00, "currency": "USD", "confidence": 0.9}},
  "payment_method": "string or null",
  "transaction_id": "string or null",
  "entities": [{{"field": "field_name", "value": "extracted_value", "confidence": 0.9}}],
  "overall_confidence": 0.85
}}"""

CONTRACT_EXTRACTION_PROMPT = """You are a legal document expert. Extract structured data from this contract text.

Document text:
```
{text}
```

Return ONLY valid JSON:
{{
  "contract_number": "string or null",
  "title": "string or null",
  "parties": ["Party A", "Party B"],
  "effective_date": "YYYY-MM-DD or null",
  "expiration_date": "YYYY-MM-DD or null",
  "total_value": {{"value": 0.00, "currency": "USD", "confidence": 0.9}},
  "key_terms": ["term1", "term2"],
  "obligations": ["obligation1"],
  "termination_clause": "string or null",
  "entities": [{{"field": "field_name", "value": "extracted_value", "confidence": 0.9}}],
  "overall_confidence": 0.85
}}"""

PROMPTS = {
    DocumentType.INVOICE: INVOICE_EXTRACTION_PROMPT,
    DocumentType.RECEIPT: RECEIPT_EXTRACTION_PROMPT,
    DocumentType.CONTRACT: CONTRACT_EXTRACTION_PROMPT,
}


def _parse_money(data: dict | None) -> MoneyAmount | None:
    if not data or not isinstance(data, dict):
        return None
    return MoneyAmount(
        value=data.get("value", 0),
        currency=data.get("currency", "USD"),
        confidence=data.get("confidence", 0.5),
    )


def _build_extracted_data(doc_type: DocumentType, data: dict):
    """Build typed extraction model from raw LLM response."""
    if doc_type == DocumentType.INVOICE:
        return InvoiceData(
            invoice_number=data.get("invoice_number"),
            date=data.get("date"),
            due_date=data.get("due_date"),
            vendor_name=data.get("vendor_name"),
            vendor_address=data.get("vendor_address"),
            buyer_name=data.get("buyer_name"),
            buyer_address=data.get("buyer_address"),
            subtotal=_parse_money(data.get("subtotal")),
            tax=_parse_money(data.get("tax")),
            total=_parse_money(data.get("total")),
            line_items=data.get("line_items", []),
            payment_terms=data.get("payment_terms"),
        )
    elif doc_type == DocumentType.RECEIPT:
        return ReceiptData(
            store_name=data.get("store_name"),
            store_address=data.get("store_address"),
            date=data.get("date"),
            time=data.get("time"),
            items=data.get("items", []),
            subtotal=_parse_money(data.get("subtotal")),
            tax=_parse_money(data.get("tax")),
            total=_parse_money(data.get("total")),
            payment_method=data.get("payment_method"),
            transaction_id=data.get("transaction_id"),
        )
    elif doc_type == DocumentType.CONTRACT:
        return ContractData(
            contract_number=data.get("contract_number"),
            title=data.get("title"),
            parties=data.get("parties", []),
            effective_date=data.get("effective_date"),
            expiration_date=data.get("expiration_date"),
            total_value=_parse_money(data.get("total_value")),
            key_terms=data.get("key_terms", []),
            obligations=data.get("obligations", []),
            termination_clause=data.get("termination_clause"),
        )
    return data


async def extract_data(text: str, doc_type: DocumentType) -> ExtractionResult:
    """Extract structured data from document text using LLM."""
    prompt_template = PROMPTS.get(doc_type)
    if not prompt_template:
        return ExtractionResult(
            document_type=doc_type,
            raw_text=text[:2000],
            extracted_data={},
            overall_confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
        )

    truncated = text[:8000]
    prompt = prompt_template.format(text=truncated)

    if not settings.OPENAI_API_KEY:
        return ExtractionResult(
            document_type=doc_type,
            raw_text=truncated,
            extracted_data={},
            overall_confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
        )

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
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

        overall_conf = content.get("overall_confidence", 0.5)
        entities = [
            ExtractedEntity(**e)
            for e in content.get("entities", [])
            if isinstance(e, dict) and "field" in e
        ]

        if overall_conf >= 0.8:
            conf_level = ConfidenceLevel.HIGH
        elif overall_conf >= 0.5:
            conf_level = ConfidenceLevel.MEDIUM
        else:
            conf_level = ConfidenceLevel.LOW

        extracted = _build_extracted_data(doc_type, content)

        return ExtractionResult(
            document_type=doc_type,
            raw_text=truncated,
            extracted_data=extracted,
            entities=entities,
            overall_confidence=overall_conf,
            confidence_level=conf_level,
        )

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return ExtractionResult(
            document_type=doc_type,
            raw_text=truncated,
            extracted_data={},
            overall_confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
        )
