"""Cross-document validation engine.

Combines LLM analysis with deterministic rule-based checks
to find discrepancies between documents.
"""
import json
import logging

import httpx

from app.config import settings
from app.models.schemas import (
    DocumentType, Discrepancy, DiscrepancyType, SeverityLevel,
    ValidationResult, ExtractionResult, InvoiceData, ReceiptData,
    MoneyAmount,
)

logger = logging.getLogger(__name__)


# ==========================================
# Rule-based validation (deterministic)
# ==========================================

def _get_total(data) -> float | None:
    """Extract total amount from extraction data."""
    if hasattr(data, "total") and data.total:
        return data.total.value
    return None


def _get_date(data) -> str | None:
    if hasattr(data, "date") and data.date:
        return data.date
    if hasattr(data, "effective_date") and data.effective_date:
        return data.effective_date
    return None


def _get_company(data) -> str | None:
    if hasattr(data, "vendor_name") and data.vendor_name:
        return data.vendor_name
    if hasattr(data, "store_name") and data.store_name:
        return data.store_name
    if hasattr(data, "parties") and data.parties:
        return data.parties[0]
    return None


def rule_based_validation(
    documents: list[tuple[str, ExtractionResult]],
) -> list[Discrepancy]:
    """Run deterministic rule-based checks across documents."""
    discrepancies = []

    for i in range(len(documents)):
        for j in range(i + 1, len(documents)):
            id_a, doc_a = documents[i]
            id_b, doc_b = documents[j]
            data_a = doc_a.extracted_data
            data_b = doc_b.extracted_data

            # --- Amount comparison ---
            total_a = _get_total(data_a)
            total_b = _get_total(data_b)
            if total_a is not None and total_b is not None:
                if abs(total_a - total_b) > 0.01:
                    severity = SeverityLevel.CRITICAL if abs(total_a - total_b) > total_a * 0.1 else SeverityLevel.WARNING
                    discrepancies.append(Discrepancy(
                        type=DiscrepancyType.AMOUNT_MISMATCH,
                        severity=severity,
                        description=f"Total amounts differ: ${total_a:.2f} vs ${total_b:.2f}",
                        document_a=id_a,
                        document_b=id_b,
                        field="total",
                        value_a=f"${total_a:.2f}",
                        value_b=f"${total_b:.2f}",
                        suggestion="Verify which amount is correct and check for calculation errors.",
                    ))

            # --- Date comparison ---
            date_a = _get_date(data_a)
            date_b = _get_date(data_b)
            if date_a and date_b and date_a != date_b:
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.DATE_MISMATCH,
                    severity=SeverityLevel.WARNING,
                    description=f"Dates differ: {date_a} vs {date_b}",
                    document_a=id_a,
                    document_b=id_b,
                    field="date",
                    value_a=date_a,
                    value_b=date_b,
                    suggestion="Confirm which date is correct.",
                ))

            # --- Company name comparison ---
            comp_a = _get_company(data_a)
            comp_b = _get_company(data_b)
            if comp_a and comp_b:
                if comp_a.lower().strip() != comp_b.lower().strip():
                    discrepancies.append(Discrepancy(
                        type=DiscrepancyType.COMPANY_MISMATCH,
                        severity=SeverityLevel.WARNING,
                        description=f"Company names differ: '{comp_a}' vs '{comp_b}'",
                        document_a=id_a,
                        document_b=id_b,
                        field="company_name",
                        value_a=comp_a,
                        value_b=comp_b,
                        suggestion="Verify the entities are the same or related.",
                    ))

            # --- Subtotal + Tax = Total check (within same doc) ---
            for doc_id, data in [(id_a, data_a), (id_b, data_b)]:
                if hasattr(data, "subtotal") and hasattr(data, "tax") and hasattr(data, "total"):
                    sub = data.subtotal.value if data.subtotal else None
                    tax = data.tax.value if data.tax else None
                    tot = data.total.value if data.total else None
                    if sub is not None and tax is not None and tot is not None:
                        expected = round(sub + tax, 2)
                        if abs(expected - tot) > 0.01:
                            discrepancies.append(Discrepancy(
                                type=DiscrepancyType.LOGICAL_ERROR,
                                severity=SeverityLevel.CRITICAL,
                                description=f"Math error: subtotal (${sub:.2f}) + tax (${tax:.2f}) = ${expected:.2f}, but total shows ${tot:.2f}",
                                document_a=doc_id,
                                document_b=doc_id,
                                field="total_calculation",
                                value_a=f"${expected:.2f} (calculated)",
                                value_b=f"${tot:.2f} (stated)",
                                suggestion="Check for calculation errors in the document.",
                            ))

    return discrepancies


# ==========================================
# LLM-based validation
# ==========================================

LLM_VALIDATION_PROMPT = """You are a forensic document analyst. Compare these documents and find any discrepancies, inconsistencies, or red flags.

{documents_text}

Look for:
- Amount mismatches between documents
- Date inconsistencies
- Different company/party names for what should be the same entity
- Missing required fields
- Logical errors (math, dates, references)
- Potential duplicate documents

Return ONLY valid JSON:
{{
  "discrepancies": [
    {{
      "type": "amount_mismatch|date_mismatch|company_mismatch|missing_field|duplicate_document|logical_error",
      "severity": "critical|warning|info",
      "description": "What's wrong",
      "document_a": "doc_id_1",
      "document_b": "doc_id_2",
      "field": "field_name",
      "value_a": "value in doc A",
      "value_b": "value in doc B",
      "suggestion": "How to fix"
    }}
  ],
  "summary": "Overall assessment",
  "risk_score": 0.0
}}"""


async def llm_validation(
    documents: list[tuple[str, str]],  # (id, text)
) -> tuple[list[Discrepancy], str, float]:
    """Use LLM to find discrepancies between documents."""
    if not settings.OPENAI_API_KEY:
        return [], "LLM not configured", 0.0

    docs_text = "\n\n".join(
        f"=== Document: {doc_id} ===\n{text[:3000]}"
        for doc_id, text in documents
    )
    prompt = LLM_VALIDATION_PROMPT.format(documents_text=docs_text)

    try:
        async with httpx.AsyncClient(timeout=120) as client:
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

        discrepancies = []
        for d in content.get("discrepancies", []):
            try:
                discrepancies.append(Discrepancy(**d))
            except Exception:
                continue

        summary = content.get("summary", "")
        risk = content.get("risk_score", 0.0)
        return discrepancies, summary, risk

    except Exception as e:
        logger.error(f"LLM validation failed: {e}")
        return [], f"LLM validation error: {e}", 0.0


# ==========================================
# Combined validation
# ==========================================

async def validate_documents(
    documents: list[tuple[str, str, ExtractionResult]],  # (id, text, extraction)
) -> ValidationResult:
    """Run full validation: rule-based + LLM hybrid approach."""
    if len(documents) < 2:
        return ValidationResult(
            is_valid=True,
            summary="Single document — cross-validation requires at least 2 documents.",
            documents_analyzed=len(documents),
            risk_score=0.0,
        )

    # Rule-based
    rule_docs = [(doc_id, ext) for doc_id, _, ext in documents]
    rule_discrepancies = rule_based_validation(rule_docs)

    # LLM-based
    llm_docs = [(doc_id, text) for doc_id, text, _ in documents]
    llm_discrepancies, llm_summary, llm_risk = await llm_validation(llm_docs)

    # Merge (deduplicate by field+type)
    seen = set()
    all_discrepancies = []
    for d in rule_discrepancies + llm_discrepancies:
        key = (d.type, d.field, d.document_a, d.document_b)
        if key not in seen:
            seen.add(key)
            all_discrepancies.append(d)

    # Calculate risk
    critical_count = sum(1 for d in all_discrepancies if d.severity == SeverityLevel.CRITICAL)
    warning_count = sum(1 for d in all_discrepancies if d.severity == SeverityLevel.WARNING)
    risk_score = min(1.0, critical_count * 0.3 + warning_count * 0.1 + llm_risk * 0.3)

    is_valid = critical_count == 0

    summary = llm_summary or f"Found {len(all_discrepancies)} discrepancies ({critical_count} critical, {warning_count} warnings)."

    return ValidationResult(
        is_valid=is_valid,
        discrepancies=all_discrepancies,
        summary=summary,
        documents_analyzed=len(documents),
        risk_score=round(risk_score, 2),
    )
