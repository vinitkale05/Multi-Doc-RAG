"use client";

import React, { useState } from "react";
import { Message, CitationDetail } from "../types";
import CitationBadge from "./CitationBadge";
import BibliographyPanel from "./BibliographyPanel";
import { submitFeedbackApi, createNoteApi } from "../lib/api";
import { Bot, User, ThumbsUp, ThumbsDown, ShieldCheck, AlertTriangle, Clock, Check, Bookmark, Pin } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
  onCitationClick: (chunkId: string) => void;
}

export default function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  const isAssistant = message.role === "assistant";
  const [feedbackRating, setFeedbackRating] = useState<number | null>(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackReason, setFeedbackReason] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [pinnedToNotes, setPinnedToNotes] = useState(false);

  const handlePinNote = async () => {
    try {
      await createNoteApi("Pinned Insight", message.content, "pinned_insight");
      setPinnedToNotes(true);
      setTimeout(() => setPinnedToNotes(false), 2500);
    } catch (e: any) {
      alert("Failed to pin note: " + e.message);
    }
  };

  const handleFeedback = async (rating: number) => {
    setFeedbackRating(rating);
    if (rating === -1) {
      setShowFeedbackModal(true);
    } else {
      try {
        await submitFeedbackApi(message.id, 1);
        setFeedbackSubmitted(true);
      } catch {}
    }
  };

  const submitReason = async () => {
    try {
      await submitFeedbackApi(message.id, -1, feedbackReason);
      setShowFeedbackModal(false);
      setFeedbackSubmitted(true);
    } catch {}
  };

  // Helper to parse answer string and render inline CitationBadge components
  const renderContentWithCitations = (content: string, citations: CitationDetail[] = []) => {
    const parts = content.split(/(\[\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        const citationId = parseInt(match[1], 10);
        const citation = citations.find((c) => c.id === citationId);
        if (citation) {
          return (
            <CitationBadge
              key={index}
              citation={citation}
              onClick={onCitationClick}
            />
          );
        }
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className={`flex space-x-3 ${isAssistant ? "items-start" : "items-start flex-row-reverse space-x-reverse"}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
          isAssistant
            ? "bg-sky-100 dark:bg-sky-950/80 text-sky-600 dark:text-sky-400 border border-sky-200 dark:border-sky-800"
            : "bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200"
        }`}
      >
        {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
      </div>

      {/* Bubble Container */}
      <div className={`flex flex-col max-w-[85%] sm:max-w-[75%] ${isAssistant ? "" : "items-end"}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isAssistant
              ? "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 shadow-sm"
              : "bg-sky-600 text-white rounded-br-none"
          }`}
        >
          <div className="whitespace-pre-wrap">
            {isAssistant
              ? renderContentWithCitations(message.content, message.citations)
              : message.content}
          </div>

          {/* Assistant Bibliography */}
          {isAssistant && message.bibliography && message.bibliography.length > 0 && (
            <BibliographyPanel
              bibliography={message.bibliography}
              citations={message.citations}
              onSelectCitation={onCitationClick}
            />
          )}
        </div>

        {/* Message Metadata & Feedback Bar for Assistant */}
        {isAssistant && (
          <div className="flex items-center space-x-3 mt-1.5 px-1 text-[11px] text-slate-400">
            {message.grounded ? (
              <span className="flex items-center space-x-1 text-emerald-600 dark:text-emerald-400 font-medium">
                <ShieldCheck className="w-3 h-3" />
                <span>Grounded with Citations</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-amber-500 font-medium">
                <AlertTriangle className="w-3 h-3" />
                <span>Insufficient Context Evidence</span>
              </span>
            )}

            {message.latency_ms && (
              <span className="flex items-center space-x-0.5 font-mono">
                <Clock className="w-2.5 h-2.5" />
                <span>{Math.round(message.latency_ms)}ms</span>
              </span>
            )}

            {message.trace_id && (
              <span className="font-mono text-[10px] hidden sm:inline">
                {message.trace_id}
              </span>
            )}

            {/* Feedback buttons */}
            <div className="flex items-center space-x-1 pl-2 border-l border-slate-200 dark:border-slate-800">
              {feedbackSubmitted ? (
                <span className="flex items-center space-x-1 text-emerald-600 text-[10px]">
                  <Check className="w-3 h-3" />
                  <span>Feedback recorded</span>
                </span>
              ) : (
                <>
                  <button
                    onClick={() => handleFeedback(1)}
                    className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition ${
                      feedbackRating === 1 ? "text-sky-600 dark:text-sky-400 font-bold" : "text-slate-400"
                    }`}
                    title="Helpful & accurate"
                  >
                    <ThumbsUp className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleFeedback(-1)}
                    className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition ${
                      feedbackRating === -1 ? "text-rose-600 font-bold" : "text-slate-400"
                    }`}
                    title="Incorrect citation or answer"
                  >
                    <ThumbsDown className="w-3 h-3" />
                  </button>
                  <button
                    onClick={handlePinNote}
                    className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition ${
                      pinnedToNotes ? "text-sky-600 font-bold" : "text-slate-400 hover:text-sky-600"
                    }`}
                    title="Pin to Studio Notes"
                  >
                    {pinnedToNotes ? <Check className="w-3 h-3 text-emerald-500" /> : <Pin className="w-3 h-3" />}
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {/* Feedback Reason Modal */}
        {showFeedbackModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl max-w-sm w-full space-y-3">
              <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-100">
                Help Us Improve RAG Grounding
              </h4>
              <textarea
                value={feedbackReason}
                onChange={(e) => setFeedbackReason(e.target.value)}
                placeholder="What was incorrect? (e.g. wrong citation, missing nuance, hallucinated fact)"
                rows={3}
                className="w-full text-xs p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setShowFeedbackModal(false)}
                  className="px-2.5 py-1 text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400"
                >
                  Cancel
                </button>
                <button
                  onClick={submitReason}
                  className="px-3 py-1 bg-sky-600 text-white rounded-md text-xs font-medium hover:bg-sky-500"
                >
                  Submit
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
