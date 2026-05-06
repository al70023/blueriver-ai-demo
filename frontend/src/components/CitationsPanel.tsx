import type { Citation } from "../types";

type CitationsPanelProps = {
  citations: Citation[];
};

export function CitationsPanel({ citations }: CitationsPanelProps) {
  return (
    <section className="panel citations-panel" aria-labelledby="citations-title">
      <div className="panel-heading">
        <h2 id="citations-title">Cited Evidence</h2>
        <span className="muted">{citations.length} chunks</span>
      </div>

      {citations.length > 0 ? (
        <div className="citation-list">
          {citations.map((citation) => (
            <article className="citation-card" key={citation.chunk_id}>
              <div className="citation-meta">
                <span>Chunk {citation.chunk_index}</span>
                <span>ID {citation.chunk_id}</span>
                <span>Score {citation.score.toFixed(3)}</span>
              </div>
              <strong>{citation.filename}</strong>
              <p>{citation.text}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="placeholder">Citation chunks returned by the backend will appear here.</p>
      )}
    </section>
  );
}
