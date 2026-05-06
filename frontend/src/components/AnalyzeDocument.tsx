type AnalyzeDocumentProps = {
  disabled: boolean;
  loading: boolean;
  onAnalyze: () => Promise<void>;
};

export function AnalyzeDocument({
  disabled,
  loading,
  onAnalyze,
}: AnalyzeDocumentProps) {
  return (
    <section className="panel analyze-panel" aria-labelledby="analyze-title">
      <div className="panel-heading">
        <h2 id="analyze-title">Analyze Document</h2>
        <button type="button" disabled={disabled || loading} onClick={onAnalyze}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>
      {disabled ? <p className="muted">Select a document before analyzing.</p> : null}
    </section>
  );
}
