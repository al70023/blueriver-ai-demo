# BlueRiver AI Review Desk

> An AI-assisted document review system with citation-backed Q&A, structured analysis, and human approval before any automated action runs.

---

## The problem this solves

BlueRiver Field Services is a 35-person operations company that manages equipment maintenance for commercial facilities. Every day they receive vendor invoices, technician service reports, customer emails, and meeting recordings — across Gmail, Drive, Airtable, Slack, and QuickBooks. The operations manager spends roughly 8 hours a week reading documents, summarizing what happened, deciding what needs follow-up, and creating tasks for the team.

Generic AI tools didn't solve this. People were copy-pasting sensitive client data into ChatGPT. Answers sounded confident but were occasionally wrong, with no way to check. Nothing was logged. Nothing was approved before action.

This system addresses that workflow head-on:

- **Documents come in.** Upload PDFs, text files, or transcripts.
- **AI summarizes and proposes actions.** Each suggested action is grounded in source citations from the original document.
- **Humans approve before anything happens.** No automated action fires without explicit human review.
- **Approved actions execute through n8n.** Once approved, the system pushes structured payloads to whatever downstream system the business uses (Slack, Airtable, QuickBooks, Google Sheets, CRM).
- **Everything is logged.** Every AI call, every approval, every webhook is recorded in an audit trail.

The result is the same speed gain a business gets from generic AI tools, with the source-grounding, control, and accountability they need to actually deploy it on real workflows.

---

## Design decisions

A few of the architectural choices are worth calling out, because they're the difference between a tutorial RAG app and something a regulated business could actually operate.

**Local embeddings instead of OpenAI's embedding API.** The system uses `sentence-transformers` running locally rather than `text-embedding-3-small`. Document content never leaves the host for the embedding step. Only the LLM call (which uses an OpenAI-compatible API) sends data out, and even that can be swapped to a local Ollama or vLLM endpoint without changing the application code. For businesses where document privacy matters more than embedding quality, this is the right tradeoff.

**Human approval is in the critical path.** AI does not take action. AI proposes actions, attaches citations, and creates `review_items` with `status: open`. A human reviews and approves. Only then does the backend fire a webhook to n8n. This adds latency. It also eliminates the failure mode where a confidently-wrong AI output triggers a real-world consequence — the largest barrier to enterprise AI adoption right now.

**Structured outputs from the LLM, not free-form text.** The `/review/analyze` endpoint expects the model to return a strict JSON shape: `summary`, `risks` (array of objects with severity and citation chunk IDs), `suggested_actions` (array with title, description, severity, citation chunk IDs). Free-form text is hard to render in a review UI and impossible to route reliably to downstream automation. Structured outputs make the rest of the system possible.

**Citations point to chunk IDs, not page numbers.** Every AI answer references specific chunks retrieved from Qdrant, and the response includes the chunk text inline so the reviewer can verify the citation without leaving the screen. This is the trust layer. Without it, "the AI said so" is the only thing a reviewer has to go on.

**Audit logs are a first-class table, not an afterthought.** `audit_logs` records every meaningful event: document uploaded, summary generated, question answered, review item created, review item approved, webhook sent. For any regulated buyer (legal, healthcare, finance), this table is non-negotiable.

**n8n as the automation layer rather than direct integrations.** The backend doesn't own integrations to Slack, Airtable, QuickBooks, Gmail, or any other downstream tool. It fires a structured webhook to n8n, and n8n handles the integration breadth. This means a new client integration is an n8n workflow change, not a code change, and the backend stays focused on the AI/review logic.

---

## Features

- PDF and TXT upload with text extraction and chunking
- Local embeddings via sentence-transformers (no document content sent to embedding API)
- Qdrant vector search over indexed chunks
- Citation-backed RAG Q&A — every answer references specific chunks the model used
- Structured document analysis — summary, risks, suggested actions, all grounded in citations
- Human-in-the-loop review queue with approve / reject states
- Approved actions trigger an n8n webhook for downstream automation
- Postgres-backed audit log of every AI call, approval, and automation event
- `/health` and `/documents/{id}/vector-status` endpoints for operational visibility

---

## Architecture

**Frontend:** React + TypeScript (Vite)
**Backend:** FastAPI (Python)
**Database:** Postgres
**Vector DB:** Qdrant
**Embeddings:** sentence-transformers (local)
**LLM:** OpenAI-compatible endpoint (defaults to OpenAI; swappable to Ollama or vLLM)
**Automation:** n8n (self-hosted via Docker Compose)

```
React Frontend
   │
   │ HTTP
   ▼
FastAPI Backend
   │
   ├── Postgres
   │     documents
   │     document_chunks
   │     review_items
   │     audit_logs
   │
   ├── sentence-transformers
   │     chunk text → embeddings (local, no external API)
   │
   ├── Qdrant
   │     semantic vector search over chunks
   │
   ├── OpenAI-compatible LLM endpoint
   │     citation-backed answers
   │     structured document analysis
   │
   └── n8n
         approved-action webhook → downstream automation
```

---

## Demo flow

1. Upload a vendor policy PDF and a vendor invoice PDF.
2. Ask: "Can this invoice be approved based on our vendor policy?"
3. Review the answer, which cites both the policy and the invoice.
4. Click **Analyze** on the invoice. The system returns a structured review: summary, risks (e.g. "missing insurance certificate"), and suggested actions (e.g. "request updated COI from Acme Vendor").
5. Approve the suggested action.
6. Watch the n8n workflow fire. Confirm the entry in the audit log.

Sample documents are provided in [`samples/`](./samples) so you can run this flow without supplying your own.

---

## Running locally

Three terminals: infrastructure, backend, frontend.

### 1. Start infrastructure

From the repo root:

```bash
cd infrastructure
docker compose up -d
```

This starts:

- Postgres on `localhost:5432`
- Qdrant on `localhost:6333`
- n8n on `localhost:5678`

### 2. Configure the backend

Create `backend/.env` from `backend/.env.example`:

```env
DATABASE_URL=postgresql+psycopg://alex:password@localhost:5432/blueriver
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
N8N_WEBHOOK_URL=http://localhost:5678/webhook/blueriver-review-action
```

Then run migrations:

```bash
cd backend
alembic upgrade head
```

### 3. Start the backend

```bash
uvicorn app.main:app --reload
```

API at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`. Health check at `http://localhost:8000/health`.

### 4. Configure and start the frontend

Create `frontend/.env` from `frontend/.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Then:

```bash
cd frontend
npm install
npm run dev
```

Frontend at `http://localhost:5173`.

### 5. Activate the n8n workflow

Open n8n at `http://localhost:5678` and ensure a workflow exists with a webhook trigger at:

```
POST http://localhost:5678/webhook/blueriver-review-action
```

A starter workflow that writes approved actions to a Google Sheet or Slack channel is recommended.

### 6. Run the demo

1. Upload `samples/vendor-policy.pdf` and `samples/invoice-acme-1042.pdf` from the [samples directory](./samples).
2. Ask: _"Can the Acme Vendor invoice be approved based on our vendor policy?"_
3. Review the cited answer.
4. Click **Analyze** on the invoice.
5. Approve the suggested action ("Request updated COI from Acme Vendor").
6. Confirm the n8n workflow fires and the audit log records the event.

---

## Evaluation

The repo includes a small eval harness in [`evals/`](./evals). It runs a fixed set of question/expected-citation pairs against the system and reports retrieval accuracy.

```bash
cd evals
python run_evals.py
```

Current baseline on the included sample corpus: see [`evals/README.md`](./evals/README.md).

---

## API reference

Base URL: `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

### Health

`GET /health` — checks API, Postgres, and Qdrant connectivity.

```json
{"api": "ok", "postgres": "ok", "qdrant": "ok"}
```

### Documents

`POST /documents/upload` — multipart file upload. Extracts text, chunks, embeds, indexes.

`GET /documents` — lists uploaded documents, newest first.

`GET /documents/{id}/chunks` — lists extracted chunks.

`GET /documents/{id}/vector-status` — compares Postgres chunk count with Qdrant vector count.

### Search and Q&A

`POST /search` — semantic search against indexed chunks.

`POST /ask` — RAG Q&A. Returns answer plus citations.

```json
{
  "question": "What obligations does this document create?",
  "document_id": 1,
  "limit": 5
}
```

Response includes `answer` and a `citations` array with chunk IDs, scores, and chunk text.

### Review

`POST /review/analyze` — generates a structured review (summary, risks, suggested actions) for a document.

`GET /review/documents/{id}/items` — lists saved suggested actions.

`POST /review/items/{id}/approve` — approves a suggested action, fires the n8n webhook, logs the event.

### Audit

`GET /audit/logs` — returns the 50 most recent audit log entries.

---

## What's not yet built

This is a v1 demo. For a real client engagement, the following would be added based on the buyer's specific requirements:

- **Local LLM mode.** A `MODEL_PROVIDER=local` setting that routes LLM calls to a local Ollama or vLLM endpoint instead of OpenAI, for clients whose data must not leave their infrastructure.
- **Audio transcription.** Upload meeting recordings, run faster-whisper locally, generate a structured summary with action items.
- **Role-based access control.** Reviewer vs. approver roles, multi-tenant workspaces.
- **Hybrid mode with redaction.** Local extraction of sensitive fields, redacted payload sent to cloud LLM for higher-quality reasoning, recombined locally.
- **Production observability.** Langfuse for LLM tracing and prompt versioning, Grafana for system metrics.
- **Eval expansion.** Larger question/citation eval set, regression checks in CI, hallucination detection.

---

## License

MIT — see [`LICENSE`](./LICENSE).

---