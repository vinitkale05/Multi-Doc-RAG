"use client";

import React, { useState } from "react";
import { CitationDetail } from "../types";
import { FileText, ChevronRight } from "lucide-react";

interface CitationBadgeProps {
  citation: CitationDetail;
  onClick: (chunkId: string) => void;
}

export default function CitationBadge({ citation, onClick }: CitationBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <span
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <button
        onClick={() => onClick(citation.chunk_id)}
        aria-label={`View citation [${citation.id}] from ${citation.title}`}
        className="citation-pill"
      >
        [{citation.id}]
      </button>

      {/* Hover preview popover */}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 bg-slate-900 text-white rounded-lg shadow-xl border border-slate-700 text-left z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-sky-400 mb-1 truncate">
            <FileText className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">{citation.title}</span>
          </div>
          <div className="flex items-center space-x-2 text-[10px] text-slate-400 mb-2">
            <span>Page {citation.page}</span>
            {citation.section && <span>• {citation.section}</span>}
            <span>• Relevance: {Math.round(citation.score * 100)}%</span>
          </div>
          <p className="text-xs text-slate-200 line-clamp-3 italic bg-slate-800/80 p-1.5 rounded border border-slate-700/50">
            "{citation.snippet}"
          </p>
          <div className="mt-2 text-[10px] text-sky-400 flex items-center justify-end font-medium">
            <span>Click to view highlighted passage</span>
            <ChevronRight className="w-3 h-3 ml-0.5" />
          </div>
        </div>
      )}
    </span>
  );
}
