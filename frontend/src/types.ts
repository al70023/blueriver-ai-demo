export type HealthResponse = {
  api: string;
  postgres: string;
  qdrant: string;
};

export type Document = {
  id: number;
  filename: string;
  created_at: string;
};

export type DocumentChunk = {
  id: number;
  document_id: number;
  chunk_index: number;
  text: string;
  created_at: string;
};

export type VectorStatus = {
  document_id: number;
  filename: string;
  postgres_chunk_count: number;
  qdrant_vector_count: number;
  in_sync: boolean;
};

export type AskRequest = {
  question: string;
  document_id: number;
  limit: number;
};

export type Citation = {
  chunk_id: number;
  document_id: number;
  filename: string;
  chunk_index: number;
  score: number;
  text: string;
};

export type AskResponse = {
  question: string;
  answer: string;
  citations: Citation[];
};
