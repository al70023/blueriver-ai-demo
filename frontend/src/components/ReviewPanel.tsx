import type { AnalyzeDocumentResponse, ReviewRisk, SuggestedAction } from "../types";

type ReviewPanelProps = {
  analysis: AnalyzeDocumentResponse | null;
  error: string | null;
  loading: boolean;
};

export function ReviewPanel({
  analysis,
  error,
  loading,
}: ReviewPanelProps) {
  return (
    <section className="panel review-panel" aria-labelledby="review-title">
      <div className="panel-heading">
        <h2 id="review-title">Document Analysis</h2>
        {loading ? <span className="muted">Analyzing...</span> : null}
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      {analysis ? (
        <div className="review-content">
          <section className="review-section" aria-labelledby="review-summary-title">
            <h3 id="review-summary-title">Summary</h3>
            <p>{analysis.summary}</p>
          </section>

          <section className="review-section" aria-labelledby="review-risks-title">
            <div className="panel-heading compact-heading">
              <h3 id="review-risks-title">Risks</h3>
              <span className="muted">{analysis.risks.length}</span>
            </div>
            {analysis.risks.length > 0 ? (
              <div className="review-list">
                {analysis.risks.map((risk, index) => (
                  <RiskCard key={`${risk.title}-${index}`} risk={risk} />
                ))}
              </div>
            ) : (
              <p className="muted">No risks returned.</p>
            )}
          </section>

          <section className="review-section" aria-labelledby="review-actions-title">
            <div className="panel-heading compact-heading">
              <h3 id="review-actions-title">Suggested Actions</h3>
              <span className="muted">{analysis.suggested_actions.length}</span>
            </div>
            {analysis.suggested_actions.length > 0 ? (
              <div className="review-list">
                {analysis.suggested_actions.map((action) => (
                  <ActionCard key={action.id} action={action} />
                ))}
              </div>
            ) : (
              <p className="muted">No suggested actions returned.</p>
            )}
          </section>
        </div>
      ) : (
        <p className="placeholder">
          Run document analysis to generate a summary, risks, and suggested reviewer actions.
        </p>
      )}
    </section>
  );
}

function RiskCard({ risk }: { risk: ReviewRisk }) {
  return (
    <article className="review-card">
      <div className="review-card-header">
        <strong>{risk.title}</strong>
        <span className="severity-pill">{risk.severity}</span>
      </div>
      <p>{risk.description}</p>
      <CitationIds ids={risk.citation_chunk_ids} />
    </article>
  );
}

function ActionCard({ action }: { action: SuggestedAction }) {
  return (
    <article className="review-card">
      <div className="review-card-header">
        <strong>{action.title}</strong>
        <span className="severity-pill">{action.severity}</span>
      </div>
      <div className="review-status">
        <span className="label">Status</span>
        <strong>{action.status}</strong>
      </div>
      <p>{action.description}</p>
      <CitationIds ids={action.citation_chunk_ids} />
    </article>
  );
}

function CitationIds({ ids }: { ids: number[] }) {
  return (
    <div className="citation-ids">
      <span className="label">Cited chunks</span>
      <span>{ids.length > 0 ? ids.join(", ") : "None"}</span>
    </div>
  );
}
