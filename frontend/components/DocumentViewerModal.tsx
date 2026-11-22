"use client";

import React, { useState, useEffect } from "react";
import { CitationPassageInfo } from "../types";
import { getCitationPassageApi } from "../lib/api";
import { X, FileText, Bookmark, ExternalLink, AlertCircle, Copy, Check } from "lucide-react";

interface DocumentViewerModalProps {
  chunkId: string | null;
  onClose: () => void;
}

export default function DocumentViewerModal({ chunkId, onClose }: DocumentViewerModalProps) {
  const [data, setData] = useState<CitationPassageInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!chunkId) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);

    getCitationPassageApi(chunkId)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Could not load citation passage");
        setLoading(false);
      });
  }, [chunkId]);

  if (!chunkId) return null;

  const copyPassage = () => {
    if (data?.text) {
      navigator.clipboard.writeText(data.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/70 dark:bg-slate-950/40">
          <div className="flex items-center space-x-2.5 truncate">
            <div className="w-8 h-8 rounded-lg bg-sky-100 dark:bg-sky-950/80 flex items-center justify-center text-sky-600 dark:text-sky-400 shrink-0">
              <FileText className="w-4 h-4" />
            </div>
            <div className="truncate">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                {data?.filename || "Source Document Passage"}
              </h3>
              <div className="flex items-center space-x-2 text-[11px] text-slate-500 dark:text-slate-400">
                <span>Page {data?.page_start ?? 1}</span>
                {data?.section_path && (
                  <>
                    <span>•</span>
                    <span className="truncate max-w-[200px]">{data.section_path}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={copyPassage}
              title="Copy snippet"
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <div className="w-6 h-6 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-slate-500">Retrieving exact document passage...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 flex items-start space-x-3 text-xs text-rose-700 dark:text-rose-300">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Retrieval Error:</span> {error}
              </div>
            </div>
          )}

          {data && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-500 pb-2 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center space-x-1.5">
                  <Bookmark className="w-3.5 h-3.5 text-sky-500" />
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    Verified Grounding Evidence
                  </span>
                </div>
                <span className="text-[10px] font-mono bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                  Chunk: {data.chunk_id.slice(0, 8)}...
                </span>
              </div>

              {/* Highlighted text container */}
              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 text-sm leading-relaxed font-serif text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
                <mark className="bg-amber-200/80 dark:bg-amber-900/60 text-slate-900 dark:text-amber-100 rounded px-1 py-0.5 shadow-sm">
                  {data.text}
                </mark>
              </div>

              <div className="text-[11px] text-slate-400 italic">
                * Note: The highlighted text above is immutable evidence extracted directly from the original document during ingestion.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/30 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">
            Source Verified & Isolated
          </span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium hover:bg-slate-300 dark:hover:bg-slate-700 transition"
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
}
