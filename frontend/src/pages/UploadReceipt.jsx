import { useCallback, useEffect, useRef, useState } from "react";
import { UploadCloud, FileText, Trash2, Eye, Sparkles } from "lucide-react";
import Button from "../components/Button";
import StatusBadge from "../components/StatusBadge";
import Modal from "../components/Modal";
import ConfirmDialog from "../components/ConfirmDialog";
import ExpenseFormModal from "../components/ExpenseFormModal";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingSpinner from "../components/LoadingSpinner";
import { useToast } from "../context/ToastContext";
import { uploadDocument, fetchDocuments, deleteDocument } from "../services/documentService";
import { extractExpenseFromDocument } from "../services/aiService";
import { createExpense } from "../services/expenseService";
import { formatDate } from "../utils/format";
import { getErrorMessage } from "../utils/errors";

const ACCEPTED_TYPES = ".jpg,.jpeg,.png,.pdf";
const ACCEPTED_MIME = ["image/jpeg", "image/png", "application/pdf"];
// Matches the backend's MAX_UPLOAD_SIZE_MB default (see backend/app/config.py).
const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export default function UploadReceipt() {
  const { showToast } = useToast();
  const fileInputRef = useRef(null);
  // Counts nested dragenter/dragleave events so the highlight doesn't flicker
  // when the pointer crosses a child element inside the drop zone.
  const dragCounterRef = useRef(0);

  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [viewingDocument, setViewingDocument] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const deletingDoc = documents.find((d) => d.id === deletingId);

  const [extractingDocId, setExtractingDocId] = useState(null);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [aiDocumentId, setAiDocumentId] = useState(null);

  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchDocuments();
      setDocuments(data);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load uploads."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  async function handleFile(file) {
    if (!file || isUploading) return;

    if (!ACCEPTED_MIME.includes(file.type)) {
      showToast("Please upload a JPG, PNG, or PDF file.", "error");
      return;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      showToast(`That file is too large. The maximum size is ${MAX_FILE_SIZE_MB}MB.`, "error");
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    try {
      const doc = await uploadDocument(file, (progressEvent) => {
        if (!progressEvent.total) return;
        setUploadProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
      });
      setDocuments((prev) => [doc, ...prev]);
      showToast(
        doc.processing_status === "completed"
          ? "Receipt uploaded and processed."
          : "Receipt uploaded, but text extraction failed."
      );
    } catch (err) {
      showToast(getErrorMessage(err, "Upload failed. Please try again."), "error");
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function handleDragEnter(e) {
    e.preventDefault();
    dragCounterRef.current += 1;
    if (e.dataTransfer.types.includes("Files")) setIsDragging(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    dragCounterRef.current = Math.max(0, dragCounterRef.current - 1);
    if (dragCounterRef.current === 0) setIsDragging(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    dragCounterRef.current = 0;
    setIsDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  }

  async function handleDeleteConfirmed() {
    setIsDeleting(true);
    try {
      await deleteDocument(deletingId);
      setDocuments((prev) => prev.filter((d) => d.id !== deletingId));
      showToast("Upload deleted.");
      setDeletingId(null);
    } catch (err) {
      showToast(getErrorMessage(err, "Failed to delete upload."), "error");
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleCreateExpenseFromReceipt(doc) {
    setExtractingDocId(doc.id);
    try {
      const suggestion = await extractExpenseFromDocument(doc.id);
      setAiSuggestion(suggestion);
      setAiDocumentId(doc.id);
    } catch (err) {
      showToast(getErrorMessage(err, "Couldn't analyze this receipt. Please try again."), "error");
    } finally {
      setExtractingDocId(null);
    }
  }

  async function handleAiExpenseSubmit(payload) {
    await createExpense(payload);
    showToast("Expense created from receipt.");
  }

  return (
    <>
      <div className="mx-auto max-w-3xl">
        <div
          onDragEnter={handleDragEnter}
          onDragOver={(e) => e.preventDefault()}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          aria-disabled={isUploading}
          className={`rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
            isDragging && !isUploading
              ? "border-accent bg-accent/5"
              : "border-gray-300 bg-white dark:border-gray-700 dark:bg-gray-900"
          }`}
        >
          {isUploading ? (
            <div className="flex flex-col items-center gap-3">
              <LoadingSpinner size="lg" />
              <p className="text-sm text-gray-600 dark:text-gray-300" role="status">
                Uploading and extracting text... {uploadProgress}%
              </p>
            </div>
          ) : (
            <>
              <UploadCloud className="mx-auto mb-3 text-gray-500 dark:text-gray-400" size={36} aria-hidden="true" />
              <p className="text-sm text-gray-700 dark:text-gray-300">Drag and drop a receipt here, or</p>
              <Button variant="secondary" className="mt-3" onClick={() => fileInputRef.current?.click()}>
                Browse files
              </Button>
              <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                JPG, JPEG, PNG, or PDF · up to {MAX_FILE_SIZE_MB}MB
              </p>
              <label htmlFor="receipt-file-input" className="sr-only">Choose a receipt file to upload</label>
              <input
                id="receipt-file-input"
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_TYPES}
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0])}
              />
            </>
          )}
        </div>

        <div className="mt-6">
          <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">Your uploads</h2>

          {isLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : error ? (
            <ErrorState message={error} onRetry={loadDocuments} />
          ) : documents.length === 0 ? (
            <EmptyState
              title="No receipts uploaded yet"
              description="Upload a receipt or bill above to extract its text automatically."
            />
          ) : (
            <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white dark:divide-gray-800 dark:border-gray-800 dark:bg-gray-900">
              {documents.map((doc) => (
                <li key={doc.id} className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex min-w-0 items-center gap-3">
                    <FileText className="shrink-0 text-gray-500 dark:text-gray-400" size={20} aria-hidden="true" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{doc.filename}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{formatDate(doc.uploaded_at)}</p>
                    </div>
                  </div>

                  <div className="flex shrink-0 flex-wrap items-center gap-2">
                    <StatusBadge status={doc.processing_status} />

                    {doc.processing_status === "completed" && (
                      <button
                        onClick={() => handleCreateExpenseFromReceipt(doc)}
                        disabled={extractingDocId === doc.id}
                        className="flex items-center gap-1 rounded-md border border-gray-300 px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                      >
                        <Sparkles size={13} aria-hidden="true" />
                        {extractingDocId === doc.id ? "Analyzing..." : "Create expense"}
                      </button>
                    )}

                    <button
                      onClick={() => setViewingDocument(doc)}
                      className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
                      aria-label={`View extracted text for ${doc.filename}`}
                      title="View extracted text"
                    >
                      <Eye size={16} aria-hidden="true" />
                    </button>
                    <button
                      onClick={() => setDeletingId(doc.id)}
                      className="rounded-md p-1.5 text-gray-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950"
                      aria-label={`Delete ${doc.filename}`}
                    >
                      <Trash2 size={16} aria-hidden="true" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <Modal isOpen={!!viewingDocument} onClose={() => setViewingDocument(null)} title={viewingDocument?.filename || "Extracted text"}>
        {viewingDocument?.processing_status === "failed" ? (
          <p className="text-sm text-red-600 dark:text-red-400">
            Text extraction failed for this file. Try re-uploading a clearer image.
          </p>
        ) : viewingDocument?.ocr_text ? (
          <pre className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-md bg-gray-50 p-3 text-sm text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            {viewingDocument.ocr_text}
          </pre>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">No text extracted yet.</p>
        )}
      </Modal>

      <ExpenseFormModal
        isOpen={!!aiSuggestion}
        onClose={() => { setAiSuggestion(null); setAiDocumentId(null); }}
        onSubmit={handleAiExpenseSubmit}
        aiSuggestion={aiSuggestion}
        documentId={aiDocumentId}
      />

      <ConfirmDialog
        isOpen={!!deletingId}
        onClose={() => setDeletingId(null)}
        onConfirm={handleDeleteConfirmed}
        isConfirming={isDeleting}
        title="Delete upload"
        message={`Are you sure you want to delete ${deletingDoc ? `"${deletingDoc.filename}"` : "this upload"}? This action cannot be undone.`}
      />
    </>
  );
}
