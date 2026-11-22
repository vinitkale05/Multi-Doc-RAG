"use client";

import React, { useState } from "react";
import { BibliographyItem, CitationDetail } from "../types";
import { BookOpen, ChevronDown, ChevronUp, FileText, ExternalLink } from "lucide-react";

interface BibliographyPanelProps {
  bibliography: BibliographyItem[];
  citations?: CitationDetail[];
  onSelectCitation: (chunkId: string) => void;
}

export default function BibliographyPanel({
  bibliography,
  citations = [],
  onSelectCitation,
}: BibliographyPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  if (!bibliography || bibliography.length === 0) return null;

  return (
    <div className="mt-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/80 dark:bg-slate-900/50 overflow-hidden text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-100/70 dark:bg-slate-800/60 font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition"
      >
        <div className="flex items-center space-x-2">
          <BookOpen className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
          <span>Cited Sources & Bibliography ({bibliography.length})</span>
        </div>
        {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {isOpen && (
        <div className="p-3 divide-y divide-slate-200 dark:divide-slate-800 space-y-2">
          {bibliography.map((item, idx) => {
            // Find citations belonging to this document
            const matchingCitations = citations.filter((c) => c.document_id === item.document_id);

            return (
              <div key={idx} className={idx > 0 ? "pt-2" : ""}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 font-medium text-slate-800 dark:text-slate-200">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    <span>{item.title}</span>
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    Pages: {item.pages.join(", ") || "1"}
                  </div>
                </div>

                {matchingCitations.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1.5 pl-5">
                    {matchingCitations.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => onSelectCitation(c.chunk_id)}
                        className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[10px] text-slate-600 dark:text-slate-300 hover:border-sky-500 dark:hover:border-sky-400 transition"
                      >
                        <span className="font-bold text-sky-600 dark:text-sky-400">[{c.id}]</span>
                        <span className="truncate max-w-[140px] italic">"{c.snippet.slice(0, 30)}..."</span>
                        <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
