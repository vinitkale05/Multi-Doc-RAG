"use client";

import React, { useState, useRef, useEffect } from "react";
import { Message, CitationDetail } from "../types";
import MessageBubble from "./MessageBubble";
import { streamChatApi } from "../lib/api";
import { Send, Square, Sparkles, Filter, AlertCircle } from "lucide-react";

interface ChatAreaProps {
  currentCollectionId: string | null;
  selectedDocIds?: string[];
  totalDocCount?: number;
  onCitationClick: (chunkId: string) => void;
  activeConversationId?: string | null;
  onNewConversationCreated?: (id: string) => void;
}

export default function ChatArea({
  currentCollectionId,
  selectedDocIds = [],
  totalDocCount = 0,
  onCitationClick,
  activeConversationId,
  onNewConversationCreated,
}: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamedText]);

  const handleSend = async (questionText?: string) => {
    const q = (questionText || input).trim();
    if (!q || isStreaming) return;

    setInput("");
    setError(null);

    // Append user message
    const userMsg: Message = {
      id: "u_" + Date.now(),
      role: "user",
      content: q,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    setIsStreaming(true);
    setStreamedText("");

    let currentTokens = "";

    await streamChatApi({
      question: q,
      conversationId: activeConversationId || undefined,
      collectionIds: currentCollectionId ? [currentCollectionId] : [],
      documentIds: selectedDocIds.length > 0 ? selectedDocIds : undefined,
      onToken: (token) => {
        currentTokens += token;
        setStreamedText(currentTokens);
      },
      onResult: (result) => {
        setIsStreaming(false);
        setStreamedText("");

        const assistantMsg: Message = {
          id: result.message_id || "a_" + Date.now(),
          role: "assistant",
          content: result.answer,
          citations: result.citations,
          bibliography: result.bibliography,
          grounded: result.grounded,
          trace_id: result.trace_id,
          latency_ms: result.latency_ms,
          created_at: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMsg]);

        if (result.conversation_id && onNewConversationCreated) {
          onNewConversationCreated(result.conversation_id);
        }
      },
      onError: (err) => {
        setIsStreaming(false);
        setStreamedText("");
        setError(err.message || "An error occurred during query generation");
      },
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const sampleQueries = [
    "Compare the renewal terms across all contracts.",
    "What is the exact procedure to rotate production API keys?",
    "What are the monthly fees and SLAs for the Enterprise support tier?",
    "What is the penalty for exceeding quantum teleportation limits?",
  ];

  return (
    <main className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] bg-white dark:bg-slate-950 overflow-hidden relative">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 max-w-4xl w-full mx-auto space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-16 max-w-lg mx-auto space-y-6 animate-in fade-in duration-300">
            <div className="w-12 h-12 rounded-2xl bg-sky-100 dark:bg-sky-950 flex items-center justify-center text-sky-600 dark:text-sky-400 border border-sky-200 dark:border-sky-800 shadow-sm">
              <Sparkles className="w-6 h-6" />
            </div>

            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Multi-Document RAG with Citations
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                Ask questions across all ingested contracts, runbooks, tables, and slides. Every factual assertion includes verifiable inline citations and exact source highlights.
              </p>
            </div>

            {/* Starter Suggestion Chips */}
            <div className="w-full space-y-2">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Example Benchmarked Queries:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                {sampleQueries.map((sq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(sq)}
                    className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/60 hover:border-sky-500 dark:hover:border-sky-500 hover:bg-sky-50/40 dark:hover:bg-sky-950/30 text-xs text-slate-700 dark:text-slate-300 transition text-left"
                  >
                    "{sq}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((m) => (
          <MessageBubble
            key={m.id}
            message={m}
            onCitationClick={onCitationClick}
          />
        ))}

        {/* Live streaming message bubble */}
        {isStreaming && (
          <div className="flex space-x-3 items-start animate-in fade-in">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-sky-100 dark:bg-sky-950/80 text-sky-600 dark:text-sky-400 border border-sky-200 dark:border-sky-800">
              <Sparkles className="w-4 h-4 animate-pulse" />
            </div>
            <div className="px-4 py-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm leading-relaxed max-w-[85%] text-slate-800 dark:text-slate-200 shadow-sm">
              <div className="whitespace-pre-wrap">
                {streamedText || "Retrieving and synthesizing grounded answer with citations..."}
                <span className="inline-block w-1.5 h-4 ml-1 bg-sky-500 animate-pulse align-middle" />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 flex items-center space-x-2 text-xs text-rose-700 dark:text-rose-300">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Query Input Footer */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md">
        <div className="max-w-4xl mx-auto space-y-2">
          {/* Active Scope Pill */}
          <div className="flex items-center space-x-2 text-[11px] text-slate-500">
            <span className="flex items-center space-x-1.5 font-medium bg-sky-50 dark:bg-sky-950/80 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800/60 px-2.5 py-0.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>
                {selectedDocIds.length > 0
                  ? `Grounding on ${selectedDocIds.length} of ${totalDocCount} sources`
                  : `Grounding on all ${totalDocCount} sources`}
              </span>
            </span>
            <span className="text-slate-400">• Press Enter to query, Shift+Enter for newline</span>
          </div>

          {/* Textarea container */}
          <div className="relative flex items-center rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 shadow-sm focus-within:ring-2 focus-within:ring-sky-500 focus-within:border-transparent transition">
            <textarea
              ref={textareaRef}
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question across your documents..."
              className="w-full resize-none p-3 pr-12 text-xs sm:text-sm bg-transparent text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none"
            />

            <div className="absolute right-2.5 flex items-center">
              {isStreaming ? (
                <button
                  onClick={() => setIsStreaming(false)}
                  className="p-1.5 rounded-lg bg-rose-500 hover:bg-rose-600 text-white transition shadow-sm"
                  title="Stop generating"
                >
                  <Square className="w-4 h-4 fill-current" />
                </button>
              ) : (
                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim()}
                  className={`p-1.5 rounded-lg transition shadow-sm ${
                    input.trim()
                      ? "bg-sky-600 hover:bg-sky-500 text-white"
                      : "bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                  }`}
                  title="Send question"
                >
                  <Send className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
