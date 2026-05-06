import type { AskResponse } from "../types";

type AnswerPanelProps = {
  response: AskResponse | null;
  error: string | null;
  loading: boolean;
};

export function AnswerPanel({ response, error, loading }: AnswerPanelProps) {
  return (
    <section className="panel answer-panel" aria-labelledby="answer-title">
      <div className="panel-heading">
        <h2 id="answer-title">Answer</h2>
        {loading ? <span className="muted">Generating...</span> : null}
      </div>
      {error ? <p className="error-text">{error}</p> : null}
      {response ? (
        <>
          <div className="asked-question">
            <span className="label">Question asked</span>
            <p>{response.question}</p>
          </div>
          <div className="answer-text">{response.answer}</div>
        </>
      ) : (
        <p className="placeholder">
          Select a document and ask a question to see the LLM answer here.
        </p>
      )}
    </section>
  );
}
