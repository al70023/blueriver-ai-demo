import { FormEvent, useState } from "react";

type AskDocumentProps = {
  disabled: boolean;
  loading: boolean;
  onAsk: (question: string, limit: number) => Promise<void>;
};

export function AskDocument({ disabled, loading, onAsk }: AskDocumentProps) {
  const [question, setQuestion] = useState("");
  const [limit, setLimit] = useState(5);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setError("Enter a question for the selected document.");
      return;
    }

    try {
      await onAsk(trimmedQuestion, limit);
    } catch (askError) {
      setError(askError instanceof Error ? askError.message : String(askError));
    }
  }

  return (
    <section className="panel" aria-labelledby="ask-title">
      <h2 id="ask-title">Ask Document</h2>
      <form className="ask-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Question</span>
          <textarea
            rows={5}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="What does this document say about eligibility, obligations, risks, or timelines?"
          />
        </label>
        <div className="ask-actions">
          <label className="field compact-field">
            <span>Limit</span>
            <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
              {[3, 5, 8, 10].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={disabled || loading || question.trim().length === 0}>
            {loading ? "Asking..." : "Ask document"}
          </button>
        </div>
      </form>
      {disabled ? <p className="muted">Upload or select a document before asking.</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
