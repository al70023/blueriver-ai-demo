import type { Document, VectorStatus } from "../types";

type DocumentSelectorProps = {
  documents: Document[];
  selectedDocument: Document | null;
  vectorStatus: VectorStatus | null;
  loading: boolean;
  vectorLoading: boolean;
  error: string | null;
  onSelect: (documentId: number) => void;
};

export function DocumentSelector({
  documents,
  selectedDocument,
  vectorStatus,
  loading,
  vectorLoading,
  error,
  onSelect,
}: DocumentSelectorProps) {
  return (
    <section className="panel" aria-labelledby="documents-title">
      <div className="panel-heading">
        <h2 id="documents-title">Documents</h2>
        {loading ? <span className="muted">Loading...</span> : null}
      </div>

      {documents.length > 0 ? (
        <label className="field">
          <span>Select document</span>
          <select
            value={selectedDocument?.id ?? ""}
            onChange={(event) => onSelect(Number(event.target.value))}
          >
            {documents.map((document) => (
              <option key={document.id} value={document.id}>
                {document.filename} (ID {document.id})
              </option>
            ))}
          </select>
        </label>
      ) : (
        <p className="muted">No documents uploaded yet.</p>
      )}

      {selectedDocument ? (
        <div className="document-meta">
          <div>
            <span className="label">Filename</span>
            <strong>{selectedDocument.filename}</strong>
          </div>
          <div>
            <span className="label">Document ID</span>
            <strong>{selectedDocument.id}</strong>
          </div>
          <div>
            <span className="label">Created</span>
            <strong>{new Date(selectedDocument.created_at).toLocaleString()}</strong>
          </div>
        </div>
      ) : null}

      <div className="vector-box">
        <div className="panel-heading">
          <h3>Vector Status</h3>
          {vectorLoading ? <span className="muted">Checking...</span> : null}
        </div>
        {error ? <p className="error-text">{error}</p> : null}
        {vectorStatus ? (
          <div className="metric-grid">
            <Metric label="Postgres chunks" value={vectorStatus.postgres_chunk_count} />
            <Metric label="Qdrant vectors" value={vectorStatus.qdrant_vector_count} />
            <Metric label="In sync" value={vectorStatus.in_sync ? "true" : "false"} />
          </div>
        ) : (
          <p className="muted">Select a document to inspect vector sync.</p>
        )}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
