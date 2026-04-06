"""Generate sample PDF documents for testing."""
import fitz  # PyMuPDF


def create_invoice_pdf(path: str):
    doc = fitz.open()
    page = doc.new_page()
    text = """
    INVOICE #INV-2026-0042

    From: TechCorp Solutions LLC
    123 Business Ave, San Francisco, CA 94102

    To: Acme Industries Inc
    456 Commerce St, New York, NY 10001

    Date: 2026-03-15
    Due Date: 2026-04-15
    Payment Terms: Net 30

    ─────────────────────────────────────────
    Description              Qty    Price    Amount
    ─────────────────────────────────────────
    Cloud Hosting (Annual)    1   $2,400.00  $2,400.00
    API Integration Service   1   $1,500.00  $1,500.00
    Premium Support Plan      1     $600.00    $600.00
    ─────────────────────────────────────────

    Subtotal:    $4,500.00
    Tax (8.5%):    $382.50
    TOTAL:       $4,882.50

    Payment Method: Wire Transfer
    Bank: First National Bank
    Account: ****7890
    """
    page.insert_text((50, 50), text, fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()


def create_receipt_pdf(path: str):
    doc = fitz.open()
    page = doc.new_page()
    text = """
    ═══════════════════════════
         TECHCORP SOLUTIONS
       123 Business Ave
       San Francisco, CA 94102
    ═══════════════════════════

    Date: 2026-03-15  Time: 14:32
    Transaction ID: TXN-88901234

    Cloud Hosting (Annual)     $2,400.00
    API Integration Service    $1,500.00
    Premium Support Plan         $600.00

    ─────────────────────────
    Subtotal:                  $4,500.00
    Tax:                         $382.50
    TOTAL:                     $4,882.50

    Payment: Visa ****4532
    Auth Code: A09871

    Thank you for your business!
    ═══════════════════════════
    """
    page.insert_text((50, 50), text, fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()


def create_mismatched_receipt_pdf(path: str):
    """Receipt with different total — for cross-validation testing."""
    doc = fitz.open()
    page = doc.new_page()
    text = """
    ═══════════════════════════
         TECHCORP SOLUTIONS
       123 Business Ave
       San Francisco, CA 94102
    ═══════════════════════════

    Date: 2026-03-16  Time: 09:15
    Transaction ID: TXN-88901299

    Cloud Hosting (Annual)     $2,400.00
    API Integration Service    $1,500.00
    Premium Support Plan         $600.00

    ─────────────────────────
    Subtotal:                  $4,500.00
    Tax:                         $405.00
    TOTAL:                     $4,905.00

    Payment: Visa ****4532

    Thank you for your business!
    ═══════════════════════════
    """
    page.insert_text((50, 50), text, fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()


def create_contract_pdf(path: str):
    doc = fitz.open()
    page = doc.new_page()
    text = """
    SERVICE AGREEMENT
    Contract No: SA-2026-0078

    This Service Agreement ("Agreement") is entered into as of March 1, 2026

    BETWEEN:
    TechCorp Solutions LLC ("Provider")
    123 Business Ave, San Francisco, CA 94102

    AND:
    Acme Industries Inc ("Client")
    456 Commerce St, New York, NY 10001

    1. TERM
    This Agreement is effective from March 1, 2026 through February 28, 2027.

    2. SERVICES
    Provider shall deliver cloud hosting, API integration, and premium support
    services as outlined in Exhibit A.

    3. COMPENSATION
    Client shall pay Provider a total of $4,882.50 for the services described herein.
    Payment is due within 30 days of invoice date.

    4. TERMINATION
    Either party may terminate this Agreement with 30 days written notice.
    Early termination fee: 20% of remaining contract value.

    5. CONFIDENTIALITY
    Both parties agree to maintain confidentiality of proprietary information.

    6. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of California.

    ________________________________    ________________________________
    TechCorp Solutions LLC              Acme Industries Inc
    Date: 2026-03-01                    Date: 2026-03-01
    """
    page.insert_text((50, 50), text, fontsize=10, fontname="helv")
    doc.save(path)
    doc.close()


if __name__ == "__main__":
    import os
    os.makedirs("../samples", exist_ok=True)
    create_invoice_pdf("../samples/invoice_sample.pdf")
    create_receipt_pdf("../samples/receipt_sample.pdf")
    create_mismatched_receipt_pdf("../samples/receipt_mismatched.pdf")
    create_contract_pdf("../samples/contract_sample.pdf")
    print("Sample documents created in samples/")
