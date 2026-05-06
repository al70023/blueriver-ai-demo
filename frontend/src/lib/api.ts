import type {
  AskRequest,
  AskResponse,
  Document,
  DocumentChunk,
  HealthResponse,
  VectorStatus,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch (error) {
    throw new Error(
      `Backend unavailable at ${API_BASE_URL}. ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message || `${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

async function readErrorMessage(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    return JSON.stringify(body);
  }

  return response.text();
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);

  return request<Document>("/documents/upload", {
    method: "POST",
    body: formData,
  });
}

export function listDocuments(): Promise<Document[]> {
  return request<Document[]>("/documents");
}

export function getDocumentChunks(documentId: number): Promise<DocumentChunk[]> {
  return request<DocumentChunk[]>(`/documents/${documentId}/chunks`);
}

export function getVectorStatus(documentId: number): Promise<VectorStatus> {
  return request<VectorStatus>(`/documents/${documentId}/vector-status`);
}

export function askDocument(payload: AskRequest): Promise<AskResponse> {
  return request<AskResponse>("/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
