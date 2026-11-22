"use client";

import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import NotebookSourcesPanel from "../components/NotebookSourcesPanel";
import ChatArea from "../components/ChatArea";
import NotebookStudioPanel from "../components/NotebookStudioPanel";
import CollectionManager from "../components/CollectionManager";
import DocumentViewerModal from "../components/DocumentViewerModal";
import { DocumentItem, Collection } from "../types";
import { getDocumentsApi, getCollectionsApi, deleteDocumentApi } from "../lib/api";
import { PanelLeft, PanelRight } from "lucide-react";

export default function Home() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);

  // Panels visibility toggles
  const [showSourcesPanel, setShowSourcesPanel] = useState(true);
  const [showStudioPanel, setShowStudioPanel] = useState(true);

  // Modals & Viewers
  const [isCollectionModalOpen, setIsCollectionModalOpen] = useState(false);
  const [selectedCitationChunkId, setSelectedCitationChunkId] = useState<string | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Initial load
  const loadCollections = async () => {
    try {
      const cols = await getCollectionsApi();
      setCollections(cols);
      if (cols.length > 0 && !selectedCollectionId) {
        setSelectedCollectionId(cols[0].id);
      }
    } catch {}
  };

  const loadDocuments = async () => {
    if (!selectedCollectionId) {
      if (collections.length > 0) {
        try {
          const docs = await getDocumentsApi(collections[0].id);
          setDocuments(docs);
          setSelectedDocIds(docs.map((d) => d.id));
        } catch {}
      }
      return;
    }
    try {
      const docs = await getDocumentsApi(selectedCollectionId);
      setDocuments(docs);
      setSelectedDocIds(docs.map((d) => d.id));
    } catch {}
  };

  useEffect(() => {
    loadCollections();
  }, []);

  useEffect(() => {
    if (collections.length > 0) {
      loadDocuments();
    }
  }, [selectedCollectionId, collections]);

  // Auto-refresh when documents are ingesting
  useEffect(() => {
    const hasActive = documents.some((d) =>
      ["QUEUED", "PARSING", "CHUNKING", "EMBEDDING"].includes(d.status)
    );
    if (!hasActive) return;
    const interval = setInterval(() => {
      loadDocuments();
    }, 2000);
    return () => clearInterval(interval);
  }, [documents, selectedCollectionId, collections]);

  const handleToggleDoc = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleSelectAll = () => {
    setSelectedDocIds(documents.map((d) => d.id));
  };

  const handleClearAll = () => {
    setSelectedDocIds([]);
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm("Are you sure you want to remove this source?")) return;
    try {
      await deleteDocumentApi(docId);
      await loadDocuments();
    } catch (err: any) {
      alert("Failed to delete source: " + err.message);
    }
  };

  const handleViewDoc = (doc: DocumentItem) => {
    // If user clicks view source, we can open citation viewer or inspect
    setIsCollectionModalOpen(true);
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      <Navbar />

      {/* Notebook Toolbar Controls */}
      <div className="h-9 px-4 border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 backdrop-blur-xs flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSourcesPanel(!showSourcesPanel)}
            className={`p-1 rounded flex items-center space-x-1.5 transition ${
              showSourcesPanel
                ? "bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 font-semibold"
                : "text-slate-400 hover:text-slate-600"
            }`}
            title="Toggle Sources Panel"
          >
            <PanelLeft className="w-3.5 h-3.5" />
            <span className="text-[11px] hidden sm:inline">Sources ({selectedDocIds.length})</span>
          </button>
        </div>

        <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 flex items-center space-x-1.5">
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            {collections.find((c) => c.id === selectedCollectionId)?.name || "Workspace"}
          </span>
          <span>•</span>
          <span>Grounded Citations</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowStudioPanel(!showStudioPanel)}
            className={`p-1 rounded flex items-center space-x-1.5 transition ${
              showStudioPanel
                ? "bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 font-semibold"
                : "text-slate-400 hover:text-slate-600"
            }`}
            title="Toggle Studio Panel"
          >
            <span className="text-[11px] hidden sm:inline">Studio</span>
            <PanelRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 3-Column Workspace */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Column: Notebook Sources Panel */}
        {showSourcesPanel && (
          <NotebookSourcesPanel
            documents={documents}
            selectedDocIds={selectedDocIds}
            onToggleDoc={handleToggleDoc}
            onSelectAll={handleSelectAll}
            onClearAll={handleClearAll}
            onAddSourceClick={() => setIsCollectionModalOpen(true)}
            onViewDoc={handleViewDoc}
            onDeleteDoc={handleDeleteDoc}
            collections={collections}
            currentCollectionId={selectedCollectionId}
            onSelectCollection={(id) => setSelectedCollectionId(id)}
            onManageCollections={() => setIsCollectionModalOpen(true)}
          />
        )}

        {/* Center Column: Grounded Chat Area */}
        <ChatArea
          currentCollectionId={selectedCollectionId}
          selectedDocIds={selectedDocIds}
          totalDocCount={documents.length}
          onCitationClick={(chunkId) => setSelectedCitationChunkId(chunkId)}
          activeConversationId={activeConversationId}
          onNewConversationCreated={(id) => setActiveConversationId(id)}
        />

        {/* Right Column: NotebookLM Studio Panel */}
        {showStudioPanel && (
          <NotebookStudioPanel
            selectedDocIds={selectedDocIds}
            currentCollectionId={selectedCollectionId}
            onOpenCitationChunk={(chunkId) => setSelectedCitationChunkId(chunkId)}
          />
        )}
      </div>

      {/* Source Upload / Collection Manager Modal */}
      <CollectionManager
        isOpen={isCollectionModalOpen}
        onClose={() => {
          setIsCollectionModalOpen(false);
          loadDocuments();
        }}
        onCollectionChange={() => {
          loadCollections();
          loadDocuments();
        }}
      />

      {/* Highlighted Document Passage Viewer */}
      <DocumentViewerModal
        chunkId={selectedCitationChunkId}
        onClose={() => setSelectedCitationChunkId(null)}
      />
    </div>
  );
}
