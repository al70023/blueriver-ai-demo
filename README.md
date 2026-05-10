# BlueRiver AI Review Desk

AI-assisted document review desk for uploading business documents, asking citation-backed questions, generating structured review findings, and sending approved actions into automation workflows.

## Features

- PDF/TXT upload
- Text extraction and chunking
- Postgres document/chunk storage
- Local embeddings with sentence-transformers
- Qdrant vector search
- RAG Q&A with citations
- Structured document analysis
- Suggested review actions
- Approve action -> n8n webhook
- Audit logging

## Architecture

Frontend: React/TypeScript  
Backend: FastAPI  
Database: Postgres  
Vector DB: Qdrant  
Automation: n8n  
LLM: OpenAI  
Embeddings: sentence-transformers

```text
React Frontend
   |
   | HTTP
   v
FastAPI Backend
   |
   |-- Postgres
   |     documents
   |     document_chunks
   |     review_items
   |     audit_logs
   |
   |-- SentenceTransformer
   |     chunk text -> embeddings
   |
   |-- Qdrant
   |     semantic vector search over chunks
   |
   |-- OpenAI
   |     citation-backed answers
   |     structured document analysis
   |
   |-- n8n
         approved action workflow
```

## Demo Flow

1. Upload document
2. Ask question
3. View citations
4. Analyze document
5. Approve suggested action
6. Send to automation webhook

## Running Locally

Run infrastructure, backend, and frontend in separate terminals.

### 1. Start Local Infrastructure

From the repo root:

```powershell
cd infrastructure
docker compose up -d
```

This starts:

- Postgres on `localhost:5432`
- Qdrant on `localhost:6333`
- n8n on `localhost:5678`

### 2. Configure Backend Environment

Create `backend/.env` from `backend/.env.example`.

For the default Docker Compose setup, use:

```env
DATABASE_URL=postgresql+psycopg://alex:password@localhost:5432/blueriver
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
N8N_WEBHOOK_URL=http://localhost:5678/webhook/blueriver-review-action
```

If this is a fresh database, run migrations from `backend/`:

```powershell
cd backend
alembic upgrade head
```

### 3. Start Backend

From `backend/`:

```powershell
uvicorn app.main:app --reload
```

The API runs at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

### 4. Configure Frontend Environment

Create `frontend/.env` from `frontend/.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 5. Start Frontend

From `frontend/`:

```powershell
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

### 6. Enable n8n Workflow

Open n8n at:

```text
http://localhost:5678
```

Make sure the workflow for the review approval webhook is active or actively listening for test executions.

The backend sends approved review items to:

```text
POST http://localhost:5678/webhook/blueriver-review-action
```

### 7. Demo Checklist

1. Open the frontend.
2. Upload a PDF or TXT document.
3. Ask a question and review the citation-backed answer.
4. Analyze the document.
5. Approve a suggested action.
6. Confirm the item status changes to `approved`.
7. Confirm n8n receives the webhook execution.

## API Reference

Base URL:

```text
http://localhost:8000
```

FastAPI interactive docs are available at:

```text
http://localhost:8000/docs
```

### Health

#### `GET /health`

Checks API, Postgres, and Qdrant connectivity.

Example response:

```json
{
  "api": "ok",
  "postgres": "ok",
  "qdrant": "ok"
}
```

### Documents

#### `POST /documents/upload`

Uploads a `.pdf` or `.txt` document. The backend extracts text, chunks it, stores chunks in Postgres, creates embeddings, and stores vectors in Qdrant.

Request:

- Content type: `multipart/form-data`
- Field: `file`

Example response:

```json
{
  "id": 1,
  "filename": "example.pdf",
  "created_at": "2026-05-09T12:00:00"
}
```

#### `GET /documents`

Lists uploaded documents, newest first.

Example response:

```json
[
  {
    "id": 1,
    "filename": "example.pdf",
    "created_at": "2026-05-09T12:00:00"
  }
]
```

#### `GET /documents/{document_id}/chunks`

Lists extracted chunks for a document.

Example response:

```json
[
  {
    "id": 10,
    "document_id": 1,
    "chunk_index": 0,
    "text": "Chunk text...",
    "created_at": "2026-05-09T12:00:00"
  }
]
```

#### `GET /documents/{document_id}/vector-status`

Compares Postgres chunk count with Qdrant vector count for a document.

Example response:

```json
{
  "document_id": 1,
  "filename": "example.pdf",
  "postgres_chunk_count": 8,
  "qdrant_vector_count": 8,
  "in_sync": true
}
```

### Search and Q&A

#### `POST /search`

Runs semantic search against document chunks. If `document_id` is omitted, search can run across indexed chunks.

Request body:

```json
{
  "query": "What are the eligibility requirements?",
  "document_id": 1,
  "limit": 5
}
```

Example response:

```json
{
  "query": "What are the eligibility requirements?",
  "matches": [
    {
      "chunk_id": 10,
      "document_id": 1,
      "filename": "example.pdf",
      "chunk_index": 0,
      "score": 0.82,
      "text": "Relevant chunk text..."
    }
  ]
}
```

#### `POST /ask`

Asks an LLM-backed question using retrieved chunks as context. Returns an answer plus citations.

Request body:

```json
{
  "question": "What obligations does this document create?",
  "document_id": 1,
  "limit": 5
}
```

Example response:

```json
{
  "question": "What obligations does this document create?",
  "answer": "The document states...",
  "citations": [
    {
      "chunk_id": 10,
      "document_id": 1,
      "filename": "example.pdf",
      "chunk_index": 0,
      "score": 0.82,
      "text": "Cited chunk text..."
    }
  ]
}
```

### Review

#### `POST /review/analyze`

Generates a structured review for a document, including summary, risks, and suggested actions.

Request body:

```json
{
  "document_id": 1,
  "max_chunks": 12
}
```

Example response:

```json
{
  "document_id": 1,
  "summary": "Brief document summary...",
  "risks": [
    {
      "title": "Missing deadline detail",
      "description": "The document references a deadline but does not define it clearly.",
      "severity": "medium",
      "citation_chunk_ids": [10]
    }
  ],
  "suggested_actions": [
    {
      "id": 3,
      "title": "Confirm deadline",
      "description": "Ask the document owner to confirm the required deadline.",
      "severity": "medium",
      "status": "open",
      "citation_chunk_ids": [10]
    }
  ]
}
```

#### `GET /review/documents/{document_id}/items`

Lists saved suggested review actions for a document.

Example response:

```json
[
  {
    "id": 3,
    "document_id": 1,
    "title": "Confirm deadline",
    "description": "Ask the document owner to confirm the required deadline.",
    "severity": "medium",
    "status": "open",
    "citation_chunk_ids": [10]
  }
]
```

#### `POST /review/items/{item_id}/approve`

Approves a suggested action, sends it to the configured n8n webhook, writes an audit log, and returns the updated item.

Example response:

```json
{
  "id": 3,
  "document_id": 1,
  "title": "Confirm deadline",
  "description": "Ask the document owner to confirm the required deadline.",
  "severity": "medium",
  "status": "approved",
  "webhook_result": {
    "sent": true,
    "status_code": 200,
    "response": "OK"
  }
}
```

If `N8N_WEBHOOK_URL` is not configured, the backend returns a successful approval with:

```json
{
  "webhook_result": {
    "sent": false,
    "reason": "N8N_WEBHOOK_URL is not configured."
  }
}
```

### Audit

#### `GET /audit/logs`

Lists the 50 most recent audit log entries.

Example response:

```json
[
  {
    "id": 1,
    "action": "review_item_approved",
    "entity_type": "review_item",
    "entity_id": 3,
    "created_at": "2026-05-09T12:00:00"
  }
]
```
