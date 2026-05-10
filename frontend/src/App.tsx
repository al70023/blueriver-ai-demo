import { useEffect, useMemo, useState } from "react";
import { AnswerPanel } from "./components/AnswerPanel";
import { AnalyzeDocument } from "./components/AnalyzeDocument";
import { AskDocument } from "./components/AskDocument";
import { CitationsPanel } from "./components/CitationsPanel";
import { DocumentSelector } from "./components/DocumentSelector";
import { HealthStatus } from "./components/HealthStatus";
import { ReviewPanel } from "./components/ReviewPanel";
import { UploadDocument } from "./components/UploadDocument";
import {
  analyzeDocument,
  approveReviewItem,
  askDocument,
  getHealth,
  getVectorStatus,
  listDocuments,
  uploadDocument,
} from "./lib/api";
import type {
  AnalyzeDocumentResponse,
  AskResponse,
  Document,
  HealthResponse,
  VectorStatus,
} from "./types";

type ResultMode = "ask" | "analysis";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);

  const [vectorStatus, setVectorStatus] = useState<VectorStatus | null>(null);
  const [vectorLoading, setVectorLoading] = useState(false);
  const [vectorError, setVectorError] = useState<string | null>(null);

  const [askResponse, setAskResponse] = useState<AskResponse | null>(null);
  const [askLoading, setAskLoading] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  const [analysis, setAnalysis] = useState<AnalyzeDocumentResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [approvingItemId, setApprovingItemId] = useState<number | null>(null);
  const [approvedItemId, setApprovedItemId] = useState<number | null>(null);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [resultMode, setResultMode] = useState<ResultMode>("ask");

  const selectedDocument = useMemo(
    () => documents.find((document) => document.id === selectedDocumentId) ?? null,
    [documents, selectedDocumentId],
  );

  useEffect(() => {
    void loadHealth();
    void loadDocuments();
  }, []);

  useEffect(() => {
    if (!selectedDocumentId) {
      setVectorStatus(null);
      return;
    }

    setAskResponse(null);
    setAskError(null);
    setAnalysis(null);
    setAnalysisError(null);
    setApprovingItemId(null);
    setApprovedItemId(null);
    setApprovalError(null);
    setResultMode("ask");
    void loadVectorStatus(selectedDocumentId);
  }, [selectedDocumentId]);

  async function loadHealth() {
    setHealthLoading(true);
    setHealthError(null);
    try {
      setHealth(await getHealth());
    } catch (error) {
      setHealthError(error instanceof Error ? error.message : String(error));
    } finally {
      setHealthLoading(false);
    }
  }

  async function loadDocuments(selectDocumentId?: number) {
    setDocumentsLoading(true);
    setDocumentsError(null);
    try {
      const nextDocuments = await listDocuments();
      setDocuments(nextDocuments);

      if (selectDocumentId) {
        setSelectedDocumentId(selectDocumentId);
      } else if (!selectedDocumentId && nextDocuments.length > 0) {
        setSelectedDocumentId(nextDocuments[0].id);
      }
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : String(error));
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function loadVectorStatus(documentId: number) {
    setVectorLoading(true);
    setVectorError(null);
    try {
      setVectorStatus(await getVectorStatus(documentId));
    } catch (error) {
      setVectorStatus(null);
      setVectorError(error instanceof Error ? error.message : String(error));
    } finally {
      setVectorLoading(false);
    }
  }

  async function handleUpload(file: File) {
    const uploadedDocument = await uploadDocument(file);
    await loadDocuments(uploadedDocument.id);
  }

  async function handleAsk(question: string, limit: number) {
    if (!selectedDocument) {
      setAskError("No document selected.");
      return;
    }

    setAskLoading(true);
    setAskError(null);
    setAskResponse(null);
    setResultMode("ask");

    try {
      const response = await askDocument({
        question,
        document_id: selectedDocument.id,
        limit,
      });
      setAskResponse(response);
    } catch (error) {
      setAskError(error instanceof Error ? error.message : String(error));
    } finally {
      setAskLoading(false);
    }
  }

  async function handleAnalyzeDocument() {
    if (!selectedDocument) {
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    setApprovalError(null);
    setApprovedItemId(null);
    setResultMode("analysis");

    try {
      const result = await analyzeDocument(selectedDocument.id);
      setAnalysis(result);
    } catch (error) {
      setAnalysisError(
        error instanceof Error ? error.message : "Failed to analyze document",
      );
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleApproveReviewItem(itemId: number) {
    setApprovingItemId(itemId);
    setApprovalError(null);
    setApprovedItemId(null);

    try {
      const approvedItem = await approveReviewItem(itemId);
      setAnalysis((currentAnalysis) => {
        if (!currentAnalysis) {
          return currentAnalysis;
        }

        return {
          ...currentAnalysis,
          suggested_actions: currentAnalysis.suggested_actions.map((action) =>
            action.id === itemId
              ? {
                  ...action,
                  status: approvedItem.status,
                }
              : action,
          ),
        };
      });
      setApprovedItemId(itemId);
    } catch (error) {
      setApprovalError(
        error instanceof Error ? error.message : "Failed to approve review item",
      );
    } finally {
      setApprovingItemId(null);
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <h1>BlueRiver AI Review Desk</h1>
          <p>Upload documents, ask questions, and get citation-backed answers.</p>
        </div>
      </header>

      <div className="top-grid">
        <HealthStatus health={health} loading={healthLoading} error={healthError} />
        <UploadDocument onUpload={handleUpload} />
      </div>

      <div className="work-grid">
        <div className="left-column">
          <DocumentSelector
            documents={documents}
            selectedDocument={selectedDocument}
            vectorStatus={vectorStatus}
            loading={documentsLoading}
            vectorLoading={vectorLoading}
            error={documentsError ?? vectorError}
            onSelect={setSelectedDocumentId}
          />
          <AskDocument
            disabled={!selectedDocument}
            loading={askLoading}
            onAsk={handleAsk}
          />
          <AnalyzeDocument
            disabled={!selectedDocument}
            loading={isAnalyzing}
            onAnalyze={handleAnalyzeDocument}
          />
        </div>
        <div className="right-column">
          {resultMode === "analysis" ? (
            <ReviewPanel
              analysis={analysis}
              approvedItemId={approvedItemId}
              approvalError={approvalError}
              approvingItemId={approvingItemId}
              error={analysisError}
              loading={isAnalyzing}
              onApprove={handleApproveReviewItem}
            />
          ) : (
            <>
              <AnswerPanel
                response={askResponse}
                error={askError}
                loading={askLoading}
              />
              <CitationsPanel citations={askResponse?.citations ?? []} />
            </>
          )}
        </div>
      </div>
    </main>
  );
}
