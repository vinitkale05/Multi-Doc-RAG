"use client";

import React, { useState, useEffect } from "react";
import { Plus, MessageSquare, Folder, Layers, Trash2 } from "lucide-react";
import { Collection, Conversation } from "../types";
import { getCollectionsApi } from "../lib/api";

interface SidebarProps {
  currentCollectionId: string | null;
  onSelectCollection: (id: string | null) => void;
  onOpenCollectionModal: () => void;
  onNewChat: () => void;
  conversations?: Conversation[];
  activeConversationId?: string | null;
  onSelectConversation?: (id: string) => void;
}

export default function Sidebar({
  currentCollectionId,
  onSelectCollection,
  onOpenCollectionModal,
  onNewChat,
  conversations = [],
  activeConversationId,
  onSelectConversation,
}: SidebarProps) {
  const [collections, setCollections] = useState<Collection[]>([]);

  useEffect(() => {
    getCollectionsApi()
      .then(setCollections)
      .catch(() => {});
  }, []);

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex flex-col h-[calc(100vh-3.5rem)] select-none">
      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Research Query</span>
        </button>
      </div>

      {/* Collections Section */}
      <div className="px-3 py-2 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
          <span>Collections</span>
          <button
            onClick={onOpenCollectionModal}
            className="text-sky-600 dark:text-sky-400 hover:underline text-[11px] font-normal normal-case flex items-center space-x-0.5"
          >
            <span>Manage</span>
          </button>
        </div>

        <div className="space-y-1 max-h-36 overflow-y-auto">
          <button
            onClick={() => onSelectCollection(null)}
            className={`w-full text-left flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition ${
              currentCollectionId === null
                ? "bg-sky-100 dark:bg-sky-950/60 text-sky-800 dark:text-sky-300 font-medium"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <div className="flex items-center space-x-2 truncate">
              <Layers className="w-3.5 h-3.5" />
              <span>All Workspace Docs</span>
            </div>
          </button>

          {collections.map((col) => (
            <button
              key={col.id}
              onClick={() => onSelectCollection(col.id)}
              className={`w-full text-left flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition ${
                currentCollectionId === col.id
                  ? "bg-sky-100 dark:bg-sky-950/60 text-sky-800 dark:text-sky-300 font-medium"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              <div className="flex items-center space-x-2 truncate">
                <Folder className="w-3.5 h-3.5 text-sky-500" />
                <span className="truncate">{col.name}</span>
              </div>
              <span className="text-[10px] text-slate-400 ml-1">
                {col.document_count ?? 0}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Conversations History */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
          Recent Queries
        </div>
        {conversations.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-400">
            No query history yet.
          </div>
        ) : (
          conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => onSelectConversation && onSelectConversation(c.id)}
              className={`w-full text-left flex items-center space-x-2 px-2.5 py-2 rounded-md text-xs transition truncate ${
                activeConversationId === c.id
                  ? "bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-white font-medium"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="truncate">{c.title || "Untitled query"}</span>
            </button>
          ))
        )}
      </div>

      {/* Quota Footer */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 text-[11px] text-slate-500 space-y-1">
        <div className="flex justify-between items-center">
          <span>Grounding Model:</span>
          <span className="font-mono text-slate-700 dark:text-slate-300">gpt-4o-mini</span>
        </div>
        <div className="flex justify-between items-center">
          <span>Embeddings:</span>
          <span className="font-mono text-slate-700 dark:text-slate-300">384-dim Hybrid</span>
        </div>
      </div>
    </aside>
  );
}
