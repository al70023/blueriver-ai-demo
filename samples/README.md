# Sample Documents

These are **fictional** documents used as sample data for the BlueRiver AI Review Desk demo. None of the people, companies, vendors, addresses, or invoices are real. Use them to run the demo without needing to supply your own data.

## Files

| File | What it is | Use it to demo |
|---|---|---|
| `vendor-policy.txt` | A vendor onboarding and invoice approval policy. Defines insurance requirements, approval tiers, hold conditions. | Citation-backed Q&A. Ask: "What insurance does a vendor need?" or "When should an invoice go on hold?" |
| `invoice-acme-1042.txt` | An invoice from a fictional vendor with a **missing Certificate of Insurance** — the document explicitly notes the COI expired on April 1, 2026. | The canonical demo case. Upload both this and the vendor policy, then ask: "Can this invoice be approved?" The system should flag the missing COI and cite the policy. |
| `service-report-greenline.txt` | A field service report with several issues identified and one customer request (a quote due May 15). | Document analysis. Run `/review/analyze` and confirm the system extracts the customer-quote follow-up as a suggested action. |
| `meeting-ops-sync-week17.txt` | A short ops meeting transcript covering the Acme COI situation, the Greenline quote, a staffing opening, and a dispatch boundary change. | Multi-action extraction from a transcript. The model should identify at least 4 distinct action items with owners and deadlines. |

## Suggested demo sequence

1. Upload `vendor-policy.txt` and `invoice-acme-1042.txt`.
2. Ask: *"Can this invoice be approved?"* → expect a "no" answer with citations to both documents.
3. Click **Analyze** on the invoice → expect a structured response identifying the missing COI as a high-severity risk and a suggested action to request updated COI.
4. Approve the suggested action → confirm the n8n webhook fires and the audit log records the event.
5. Bonus: upload `meeting-ops-sync-week17.txt` and run **Analyze** to demonstrate multi-action extraction from a transcript.

## Why text files instead of PDFs?

The repo ships these as `.txt` so they render in the GitHub web UI and so anyone can read them without downloading. For a fuller demo, generate PDF versions using any tool you like (LibreOffice, `pandoc`, `wkhtmltopdf`) — the BlueRiver upload pipeline accepts both.

A simple conversion using pandoc:

```bash
for f in *.txt; do
  pandoc "$f" -o "${f%.txt}.pdf"
done
```

## A note on realism

These documents are deliberately a notch more detailed than typical "lorem ipsum" sample data because the demo needs the AI to find specific facts and cite them. The vendor policy includes specific dollar thresholds and time windows. The invoice references specific PO numbers and a specific COI expiration date. The service report has named follow-up actions with owners and deadlines. This is what real business documents look like, and it's what the system is built to handle.

If you replace these with your own documents, aim for the same shape: real structure, named entities, specific dates, and at least one piece of information the AI has to reason about (a missing field, a deadline, a conditional rule).