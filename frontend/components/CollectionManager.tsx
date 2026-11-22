"use client";

import React, { useState, useEffect } from "react";
import { Collection, DocumentItem } from "../types";
import {
  getCollectionsApi,
  createCollectionApi,
  deleteCollectionApi,
  getDocumentsApi,
  uploadDocumentsApi,
  ingestUrlApi,
  deleteDocumentApi,
  retryDocumentApi,
} from "../lib/api";
import {
  X,
  UploadCloud,
  Globe,
  FolderPlus,
  Trash2,
  FileText,
  AlertCircle,
  CheckCircle2,
  Clock,
  Layers,
  RotateCw,
} from "lucide-react";

interface CollectionManagerProps {
  isOpen: boolean;
  onClose: () => void;
  onCollectionChange: () => void;
}

export default function CollectionManager({
  isOpen,
  onClose,
  onCollectionChange,
}: CollectionManagerProps) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedColId, setSelectedColId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  // New Collection Form
  const [showNewCol, setShowNewCol] = useState(false);
  const [newColName, setNewColName] = useState("");
  const [newColDesc, setNewColDesc] = useState("");

  // URL Ingest Form
  const [showUrlModal, setShowUrlModal] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [urlTitle, setUrlTitle] = useState("");

  const loadCollections = async () => {
    try {
      const cols = await getCollectionsApi();
      setCollections(cols);
      if (cols.length > 0 && !selectedColId) {
        setSelectedColId(cols[0].id);
      }
    } catch {}
  };

  const loadDocuments = async (colId: string) => {
    try {
      setLoading(true);
      const docs = await getDocumentsApi(colId);
      setDocuments(docs);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadCollections();
    }
  }, [isOpen]);

  useEffect(() => {
    if (selectedColId) {
      loadDocuments(selectedColId);
    }
  }, [selectedColId]);

  // Auto-refresh when any document is currently in ingestion progress
  useEffect(() => {
    const hasActiveIngestion = documents.some((d) =>
      ["QUEUED", "PARSING", "CHUNKING", "EMBEDDING"].includes(d.status)
    );
    if (!hasActiveIngestion || !selectedColId || !isOpen) return;

    const timer = setInterval(() => {
      loadDocuments(selectedColId);
      onCollectionChange();
    }, 2000);
    return () => clearInterval(timer);
  }, [documents, selectedColId, isOpen]);

  if (!isOpen) return null;

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColName.trim()) return;
    try {
      const created = await createCollectionApi(newColName, newColDesc);
      setNewColName("");
      setNewColDesc("");
      setShowNewCol(false);
      await loadCollections();
      setSelectedColId(created.id);
      onCollectionChange();
    } catch (err: any) {
      alert(err.message || "Failed to create collection");
    }
  };

  const handleDeleteCollection = async (colId: string) => {
    if (!confirm("Are you sure? This will delete the collection, documents, chunks and vectors.")) return;
    try {
      await deleteCollectionApi(colId);
      setSelectedColId(null);
      await loadCollections();
      onCollectionChange();
    } catch (err: any) {
      alert(err.message || "Failed to delete collection");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !selectedColId) return;
    const filesArray = Array.from(e.target.files);
    try {
      setUploading(true);
      await uploadDocumentsApi(selectedColId, filesArray);
      setUploading(false);
      await loadDocuments(selectedColId);
      onCollectionChange();
    } catch (err: any) {
      setUploading(false);
      alert(err.message || "Upload failed");
    }
  };

  const handleUrlIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim() || !selectedColId) return;
    try {
      await ingestUrlApi(selectedColId, urlInput, urlTitle || undefined);
      setUrlInput("");
      setUrlTitle("");
      setShowUrlModal(false);
      await loadDocuments(selectedColId);
      onCollectionChange();
    } catch (err: any) {
      alert(err.message || "URL ingestion failed");
    }
  };

  const handleRetryDocument = async (docId: string) => {
    try {
      await retryDocumentApi(docId);
      if (selectedColId) {
        await loadDocuments(selectedColId);
      }
      onCollectionChange();
    } catch (err: any) {
      alert(err.message || "Retry failed");
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm("Delete this document and its indexed vectors?")) return;
    try {
      await deleteDocumentApi(docId);
      if (selectedColId) {
        await loadDocuments(selectedColId);
      }
      onCollectionChange();
    } catch (err: any) {
      alert(err.message || "Failed to delete document");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-4xl bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/70 dark:bg-slate-950/40">
          <div className="flex items-center space-x-2">
            <Layers className="w-5 h-5 text-sky-600 dark:text-sky-400" />
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Document Collections & Ingestion Library
            </h2>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-md">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Columns */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Collections List */}
          <div className="w-1/3 border-r border-slate-200 dark:border-slate-800 p-4 flex flex-col justify-between bg-slate-50/30 dark:bg-slate-900/30">
            <div className="space-y-2 overflow-y-auto flex-1">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase">
                <span>Collections</span>
                <button
                  onClick={() => setShowNewCol(true)}
                  className="text-sky-600 dark:text-sky-400 flex items-center space-x-1 hover:underline text-[11px]"
                >
                  <FolderPlus className="w-3.5 h-3.5" />
                  <span>New</span>
                </button>
              </div>

              {collections.map((col) => (
                <div
                  key={col.id}
                  onClick={() => setSelectedColId(col.id)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition flex items-start justify-between ${
                    selectedColId === col.id
                      ? "border-sky-500 bg-sky-50/80 dark:bg-sky-950/50 text-sky-950 dark:text-sky-200"
                      : "border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800/50"
                  }`}
                >
                  <div className="truncate pr-2">
                    <div className="font-semibold truncate">{col.name}</div>
                    <div className="text-[11px] text-slate-400 truncate">{col.description || "No description"}</div>
                    <div className="text-[10px] text-slate-500 mt-1">{col.document_count ?? 0} documents</div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteCollection(col.id);
                    }}
                    title="Delete collection"
                    className="p-1 text-slate-400 hover:text-rose-500 rounded"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>

            {/* Ingestion limits badge */}
            <div className="pt-3 border-t border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 space-y-0.5">
              <div>Max File Size: 50 MB</div>
              <div>Formats: PDF, DOCX, PPTX, XLSX, CSV, TXT, HTML</div>
              <div>Protection: SSRF & Injection defanged</div>
            </div>
          </div>

          {/* Right: Selected Collection Documents */}
          <div className="flex-1 p-6 flex flex-col justify-between overflow-y-auto">
            {selectedColId ? (
              <div className="space-y-4">
                {/* Upload Action Bar */}
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                    Documents in Collection
                  </h3>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setShowUrlModal(true)}
                      className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-200 flex items-center space-x-1.5 transition"
                    >
                      <Globe className="w-3.5 h-3.5 text-sky-500" />
                      <span>Ingest URL</span>
                    </button>

                    <label className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium flex items-center space-x-1.5 cursor-pointer shadow-sm transition">
                      <UploadCloud className="w-3.5 h-3.5" />
                      <span>{uploading ? "Uploading..." : "Upload Files"}</span>
                      <input
                        type="file"
                        multiple
                        className="hidden"
                        onChange={handleFileUpload}
                        disabled={uploading}
                        accept=".pdf,.docx,.pptx,.xlsx,.xls,.csv,.txt,.html,.md"
                      />
                    </label>
                  </div>
                </div>

                {/* Documents List */}
                <div className="space-y-2">
                  {documents.length === 0 ? (
                    <div className="border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center text-xs text-slate-400 space-y-2">
                      <UploadCloud className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-600" />
                      <div>No documents uploaded to this collection yet.</div>
                      <div className="text-[11px] text-slate-500">Upload PDF, DOCX, CSV or ingest web pages to start querying.</div>
                    </div>
                  ) : (
                    documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between text-xs shadow-xs"
                      >
                        <div className="flex items-center space-x-3 truncate">
                          <FileText className="w-4 h-4 text-sky-500 shrink-0" />
                          <div className="truncate">
                            <div className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                              {doc.filename}
                            </div>
                            <div className="text-[10px] text-slate-400 flex items-center space-x-2">
                              <span>{(doc.size / 1024).toFixed(1)} KB</span>
                              <span>• Pages: {doc.page_count}</span>
                              <span className="font-mono">SHA: {doc.sha256.slice(0, 8)}...</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          {/* Status Badge */}
                          <span
                            title={doc.error || doc.status}
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center space-x-1 ${
                              doc.status === "READY"
                                ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300"
                                : doc.status === "FAILED"
                                ? "bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300"
                                : "bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 animate-pulse"
                            }`}
                          >
                            {doc.status === "READY" && <CheckCircle2 className="w-2.5 h-2.5" />}
                            {doc.status === "FAILED" && <AlertCircle className="w-2.5 h-2.5" />}
                            {["QUEUED", "PARSING", "CHUNKING", "EMBEDDING"].includes(doc.status) && (
                              <Clock className="w-2.5 h-2.5 animate-spin" />
                            )}
                            <span>{doc.status}</span>
                          </span>

                          {doc.status === "FAILED" && (
                            <button
                              onClick={() => handleRetryDocument(doc.id)}
                              className="p-1 text-sky-500 hover:text-sky-600 dark:hover:text-sky-400 rounded hover:bg-sky-50 dark:hover:bg-slate-800 transition"
                              title={`Retry ingestion: ${doc.error || 'Click to retry'}`}
                            >
                              <RotateCw className="w-3.5 h-3.5" />
                            </button>
                          )}

                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="p-1 text-slate-400 hover:text-rose-500 rounded"
                            title="Delete file"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-16 text-xs text-slate-400">
                Select a collection on the left or create a new one.
              </div>
            )}
          </div>
        </div>

        {/* Modal: New Collection */}
        {showNewCol && (
          <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
            <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-sm w-full space-y-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Create New Collection</h3>
              <form onSubmit={handleCreateCollection} className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Name</label>
                  <input
                    type="text"
                    required
                    value={newColName}
                    onChange={(e) => setNewColName(e.target.value)}
                    placeholder="e.g. Legal Contracts 2026"
                    className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Description</label>
                  <textarea
                    rows={2}
                    value={newColDesc}
                    onChange={(e) => setNewColDesc(e.target.value)}
                    placeholder="Collection purpose and scope..."
                    className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white mt-1"
                  />
                </div>
                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowNewCol(false)}
                    className="px-3 py-1.5 text-xs text-slate-500 hover:text-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-medium shadow-sm"
                  >
                    Create Collection
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: URL Ingest */}
        {showUrlModal && (
          <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
            <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-sm w-full space-y-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Ingest Web Page via URL</h3>
              <form onSubmit={handleUrlIngest} className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Page URL</label>
                  <input
                    type="url"
                    required
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://example.com/research-paper"
                    className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Custom Title (Optional)</label>
                  <input
                    type="text"
                    value={urlTitle}
                    onChange={(e) => setUrlTitle(e.target.value)}
                    placeholder="e.g. Acme API Specs"
                    className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white mt-1"
                  />
                </div>
                <div className="text-[10px] text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-2 rounded border border-slate-200 dark:border-slate-800">
                  SSRF Protection: Hostname DNS is checked against private IP ranges (10.x, 172.16.x, 192.168.x, 127.x, 169.254.x cloud metadata).
                </div>
                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowUrlModal(false)}
                    className="px-3 py-1.5 text-xs text-slate-500 hover:text-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-medium shadow-sm"
                  >
                    Ingest URL
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
