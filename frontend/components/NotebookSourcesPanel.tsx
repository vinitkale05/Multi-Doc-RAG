"use client";

import React, { useState } from "react";
import { DocumentItem, Collection } from "../types";
import {
  FileText,
  Plus,
  CheckSquare,
  Square,
  Trash2,
  ExternalLink,
  Layers,
  Search,
  Filter,
} from "lucide-react";

interface NotebookSourcesPanelProps {
  documents: DocumentItem[];
  selectedDocIds: string[];
  onToggleDoc: (docId: string) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
  onAddSourceClick: () => void;
  onViewDoc: (doc: DocumentItem) => void;
  onDeleteDoc: (docId: string) => void;
  collections: Collection[];
  currentCollectionId: string | null;
  onSelectCollection: (id: string | null) => void;
  onManageCollections: () => void;
}

export default function NotebookSourcesPanel({
  documents,
  selectedDocIds,
  onToggleDoc,
  onSelectAll,
  onClearAll,
  onAddSourceClick,
  onViewDoc,
  onDeleteDoc,
  collections,
  currentCollectionId,
  onSelectCollection,
  onManageCollections,
}: NotebookSourcesPanelProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const allSelected = documents.length > 0 && selectedDocIds.length === documents.length;

  return (
    <div className="w-80 h-full border-r border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/40 flex flex-col select-none shrink-0">
      {/* Panel Top Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight">
              Sources
            </h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold">
              {selectedDocIds.length}/{documents.length}
            </span>
          </div>

          <button
            onClick={onManageCollections}
            className="text-[11px] text-sky-600 dark:text-sky-400 hover:underline flex items-center space-x-1"
          >
            <Layers className="w-3 h-3" />
            <span>Collections</span>
          </button>
        </div>

        {/* Add Source Primary Button */}
        <button
          onClick={onAddSourceClick}
          className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>Add sources</span>
        </button>

        {/* Search & Bulk Select Controls */}
        <div className="space-y-2">
          <div className="relative flex items-center">
            <Search className="w-3.5 h-3.5 absolute left-2.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search sources..."
              className="w-full text-xs pl-8 pr-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 px-0.5">
            <button
              onClick={allSelected ? onClearAll : onSelectAll}
              className="hover:text-sky-600 dark:hover:text-sky-400 flex items-center space-x-1 font-medium"
            >
              {allSelected ? <CheckSquare className="w-3.5 h-3.5 text-sky-600" /> : <Square className="w-3.5 h-3.5" />}
              <span>{allSelected ? "Deselect all" : "Select all"}</span>
            </button>
            <span className="text-[10px] text-slate-400">
              Check to ground queries
            </span>
          </div>
        </div>
      </div>

      {/* Sources List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
        {filteredDocs.length === 0 ? (
          <div className="text-center py-12 px-4 space-y-2 text-slate-400 text-xs">
            <FileText className="w-8 h-8 mx-auto opacity-40" />
            <p>No sources found.</p>
            <button
              onClick={onAddSourceClick}
              className="text-sky-600 dark:text-sky-400 hover:underline font-semibold text-[11px]"
            >
              Upload PDF, DOCX, CSV or URLs
            </button>
          </div>
        ) : (
          filteredDocs.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);

            return (
              <div
                key={doc.id}
                onClick={() => onToggleDoc(doc.id)}
                className={`p-2.5 rounded-xl border text-xs cursor-pointer transition flex items-start justify-between group ${
                  isSelected
                    ? "bg-white dark:bg-slate-900 border-sky-300 dark:border-sky-800/80 shadow-xs ring-1 ring-sky-500/20"
                    : "bg-slate-100/50 dark:bg-slate-900/20 border-slate-200 dark:border-slate-800/60 opacity-60 hover:opacity-100"
                }`}
              >
                <div className="flex items-start space-x-2.5 truncate pr-2">
                  <div className="mt-0.5 text-sky-600 dark:text-sky-400 shrink-0">
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 fill-sky-100 dark:fill-sky-950" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                  <div className="truncate">
                    <div className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                      {doc.filename}
                    </div>
                    <div className="flex items-center space-x-1.5 text-[10px] text-slate-400 mt-0.5">
                      <span>{(doc.size / 1024).toFixed(0)} KB</span>
                      <span>•</span>
                      <span>{doc.page_count} page{doc.page_count === 1 ? "" : "s"}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-1 shrink-0 opacity-0 group-hover:opacity-100 transition">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onViewDoc(doc);
                    }}
                    title="Preview source"
                    className="p-1 text-slate-400 hover:text-sky-600 rounded"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteDoc(doc.id);
                    }}
                    title="Remove source"
                    className="p-1 text-slate-400 hover:text-rose-500 rounded"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Collection Switcher Footer */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/60 text-xs">
        <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
          Active Workspace
        </label>
        <select
          value={currentCollectionId || ""}
          onChange={(e) => onSelectCollection(e.target.value || null)}
          className="w-full p-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
        >
          <option value="">All Ingested Documents</option>
          {collections.map((col) => (
            <option key={col.id} value={col.id}>
              {col.name} ({col.document_count ?? 0})
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
