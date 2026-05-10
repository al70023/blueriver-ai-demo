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
- Approve action → n8n webhook
- Audit logging


## Architecture

Frontend: React/TypeScript
Backend: FastAPI
Database: Postgres
Vector DB: Qdrant
Automation: n8n
LLM: OpenAI
Embeddings: sentence-transformers

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
   |     text → embeddings
   |
   |-- Qdrant
   |     vector search over chunks
   |
   |-- OpenAI
   |     grounded answers + structured review
   |
   |-- n8n
         approved action workflow


## Demo Flow

1. Upload document
2. Ask question
3. View citations
4. Analyze document
5. Approve suggested action
6. Send to automation webhook


## Running Locally

...

