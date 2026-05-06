import { FormEvent, useState } from "react";

type UploadDocumentProps = {
  onUpload: (file: File) => Promise<void>;
};

export function UploadDocument({ onUpload }: UploadDocumentProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    setError(null);
    setSuccess(null);

    if (!file) {
      setError("Choose a PDF or TXT document first.");
      return;
    }

    if (!/\.(pdf|txt)$/i.test(file.name)) {
      setError("Unsupported file type. Upload a .pdf or .txt file.");
      return;
    }

    setLoading(true);
    try {
      await onUpload(file);
      setSuccess(`${file.name} uploaded and selected.`);
      setFile(null);
      form.reset();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : String(uploadError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel" aria-labelledby="upload-title">
      <h2 id="upload-title">Upload Document</h2>
      <form className="upload-form" onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>
      {error ? <p className="error-text">{error}</p> : null}
      {success ? <p className="success-text">{success}</p> : null}
    </section>
  );
}
