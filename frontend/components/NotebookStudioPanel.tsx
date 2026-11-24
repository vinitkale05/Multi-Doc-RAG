"use client";

import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import {
  AudioOverviewData,
  StudioArtifactData,
  NoteItem,
  DocumentItem,
} from "../types";
import {
  generateAudioOverviewApi,
  generateStudyGuideApi,
  generateBriefingDocApi,
  generateFaqApi,
  generateTimelineApi,
  getNotesApi,
  createNoteApi,
  deleteNoteApi,
} from "../lib/api";
import {
  Headphones,
  BookOpen,
  FileText,
  HelpCircle,
  Clock,
  Sparkles,
  Play,
  Pause,
  RotateCcw,
  Plus,
  Trash2,
  Copy,
  Check,
  X,
  Bookmark,
  Loader2,
} from "lucide-react";

interface NotebookStudioPanelProps {
  selectedDocIds: string[];
  currentCollectionId: string | null;
  onOpenCitationChunk?: (chunkId: string) => void;
}

export default function NotebookStudioPanel({
  selectedDocIds,
  currentCollectionId,
}: NotebookStudioPanelProps) {
  // Audio Overview State
  const [audioOverview, setAudioOverview] = useState<AudioOverviewData | null>(null);
  const [generatingAudio, setGeneratingAudio] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTurnIdx, setCurrentTurnIdx] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);

  // Studio Artifact Viewer State
  const [activeArtifact, setActiveArtifact] = useState<StudioArtifactData | null>(null);
  const [generatingArtifactType, setGeneratingArtifactType] = useState<string | null>(null);

  // Notes State
  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [showNewNoteModal, setShowNewNoteModal] = useState(false);
  const [newNoteTitle, setNewNoteTitle] = useState("");
  const [newNoteContent, setNewNoteContent] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    loadNotes();
  }, []);

  // Web Speech Synthesis Ref
  const speechUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const loadNotes = async () => {
    try {
      const data = await getNotesApi();
      setNotes(data);
    } catch {}
  };

  // Generate Audio Overview
  const handleGenerateAudio = async () => {
    setGeneratingAudio(true);
    try {
      const data = await generateAudioOverviewApi(selectedDocIds, currentCollectionId || undefined);
      setAudioOverview(data);
      setCurrentTurnIdx(0);
      setIsPlaying(false);
    } catch (err: any) {
      alert("Audio generation error: " + (err.message || "Failed to generate Audio Overview"));
    } finally {
      setGeneratingAudio(false);
    }
  };

  // Web Speech Synthesis Audio Player
  const playDialogueFrom = (index: number) => {
    if (!audioOverview || index >= audioOverview.dialogue.length) {
      setIsPlaying(false);
      setCurrentTurnIdx(0);
      return;
    }

    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Web Speech API is not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();
    setCurrentTurnIdx(index);
    setIsPlaying(true);

    const turn = audioOverview.dialogue[index];
    const utterance = new SpeechSynthesisUtterance(`${turn.speaker} says: ${turn.text}`);
    speechUtteranceRef.current = utterance;
    utterance.rate = playbackSpeed;

    // Distinguish voices between Alex and Taylor
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      if (turn.speaker === "Alex") {
        utterance.pitch = 1.0;
        utterance.voice = voices.find((v) => v.name.includes("Male") || v.lang.startsWith("en")) || voices[0];
      } else {
        utterance.pitch = 1.25;
        utterance.voice = voices.find((v) => v.name.includes("Female") || v.lang.startsWith("en")) || voices[0];
      }
    }

    utterance.onend = () => {
      playDialogueFrom(index + 1);
    };

    utterance.onerror = () => {
      setIsPlaying(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  const togglePlayAudio = () => {
    if (typeof window === "undefined") return;
    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      playDialogueFrom(currentTurnIdx);
    }
  };

  const resetAudio = () => {
    if (typeof window === "undefined") return;
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setCurrentTurnIdx(0);
  };

  // Generate Studio Artifacts
  const handleGenerateArtifact = async (type: "study_guide" | "briefing_doc" | "faq" | "timeline") => {
    setGeneratingArtifactType(type);
    try {
      let res: StudioArtifactData;
      if (type === "study_guide") {
        res = await generateStudyGuideApi(selectedDocIds, currentCollectionId || undefined);
      } else if (type === "briefing_doc") {
        res = await generateBriefingDocApi(selectedDocIds, currentCollectionId || undefined);
      } else if (type === "faq") {
        res = await generateFaqApi(selectedDocIds, currentCollectionId || undefined);
      } else {
        res = await generateTimelineApi(selectedDocIds, currentCollectionId || undefined);
      }
      setActiveArtifact(res);
    } catch (err: any) {
      alert("Error generating " + type + ": " + (err.message || "Failed"));
    } finally {
      setGeneratingArtifactType(null);
    }
  };

  // Notes actions
  const handleCreateNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteTitle.trim()) return;
    try {
      await createNoteApi(newNoteTitle, newNoteContent, "user_note", currentCollectionId || undefined);
      setNewNoteTitle("");
      setNewNoteContent("");
      setShowNewNoteModal(false);
      await loadNotes();
    } catch (err: any) {
      alert("Failed to create note: " + err.message);
    }
  };

  const handleSaveArtifactAsNote = async () => {
    if (!activeArtifact) return;
    try {
      await createNoteApi(
        activeArtifact.title,
        activeArtifact.content_markdown,
        activeArtifact.artifact_type,
        currentCollectionId || undefined
      );
      await loadNotes();
      alert("Saved to Studio Notes!");
    } catch (err: any) {
      alert("Failed to save note: " + err.message);
    }
  };

  const handleDeleteNote = async (id: string) => {
    try {
      await deleteNoteApi(id);
      await loadNotes();
    } catch (err: any) {
      alert("Failed to delete note: " + err.message);
    }
  };

  const copyNoteText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="w-84 h-full border-l border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/40 flex flex-col select-none shrink-0 overflow-y-auto">
      {/* Studio Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-sky-600 dark:text-sky-400" />
          <h2 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight">
            Studio
          </h2>
        </div>
        <span className="text-[10px] font-medium text-slate-400">
          NotebookLM Tools
        </span>
      </div>

      <div className="p-4 space-y-6">
        {/* =================================================================== */}
        {/* 1. AUDIO OVERVIEW (DEEP DIVE PODCAST)                               */}
        {/* =================================================================== */}
        <div className="rounded-2xl border border-sky-200 dark:border-sky-900/60 bg-gradient-to-br from-sky-50/80 to-indigo-50/50 dark:from-sky-950/40 dark:to-indigo-950/20 p-4 space-y-3 shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-sky-600 text-white flex items-center justify-center shadow-xs">
                <Headphones className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                  Audio Overview
                </h3>
                <span className="text-[10px] text-sky-700 dark:text-sky-400 font-medium">
                  Deep Dive Podcast
                </span>
              </div>
            </div>

            <button
              onClick={handleGenerateAudio}
              disabled={generatingAudio}
              className={`px-2.5 py-1 rounded-lg text-white text-[11px] font-medium shadow-xs transition flex items-center gap-1.5
                ${generatingAudio ? "bg-sky-700 cursor-not-allowed" : "bg-sky-600 hover:bg-sky-500"}`}
            >
              {generatingAudio && <Loader2 className="w-3 h-3 animate-spin" />}
              {generatingAudio ? "Synthesizing..." : audioOverview ? "Regenerate" : "Generate"}
            </button>
          </div>

          <p className="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed">
            Two AI hosts (Alex & Taylor) unpack and discuss your selected sources in a conversational, deep-dive dialogue.
          </p>

          {/* Interactive Player if generated */}
          {audioOverview && (
            <div className="pt-2 border-t border-sky-200 dark:border-sky-800/60 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-800 dark:text-slate-200 truncate pr-2">
                  {audioOverview.title}
                </span>
                <button
                  onClick={() => setPlaybackSpeed(playbackSpeed === 1 ? 1.5 : 1)}
                  className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-sky-200/60 dark:bg-sky-900/60 text-sky-800 dark:text-sky-300"
                >
                  {playbackSpeed}x
                </button>
              </div>

              {/* Controls */}
              <div className="flex items-center justify-center space-x-3 py-1">
                <button
                  onClick={resetAudio}
                  title="Reset"
                  className="p-1.5 text-slate-500 hover:text-slate-700 dark:text-slate-400 rounded-full hover:bg-white/60 dark:hover:bg-slate-800/60"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={togglePlayAudio}
                  className="w-9 h-9 rounded-full bg-sky-600 hover:bg-sky-500 text-white flex items-center justify-center shadow-md transition"
                >
                  {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
                </button>
              </div>

              {/* Live Dialogue Transcript */}
              <div className="max-h-40 overflow-y-auto space-y-2 p-2 rounded-xl bg-white/70 dark:bg-slate-950/60 border border-sky-100 dark:border-sky-900 text-[11px]">
                {audioOverview.dialogue.map((turn, idx) => (
                  <div
                    key={idx}
                    onClick={() => playDialogueFrom(idx)}
                    className={`p-1.5 rounded-lg cursor-pointer transition ${
                      currentTurnIdx === idx && isPlaying
                        ? "bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100 font-medium"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span className="font-bold text-sky-600 dark:text-sky-400">{turn.speaker}</span>
                      <span>{turn.timestamp}</span>
                    </div>
                    <p className="mt-0.5 line-clamp-2">{turn.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* =================================================================== */}
        {/* 2. ONE-CLICK STUDIO GENERATORS                                      */}
        {/* =================================================================== */}
        <div className="space-y-2">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Synthesize from Sources
          </div>

          <div className="grid grid-cols-2 gap-2">
            {/* Study Guide */}
            <div className="relative">
              {generatingArtifactType === "study_guide" && (
                <>
                  <span className="absolute -inset-[2px] rounded-xl pointer-events-none z-10 animate-pulse bg-gradient-to-br from-sky-400 via-blue-500 to-sky-400 opacity-70" />
                  <span className="absolute -inset-[2px] rounded-xl pointer-events-none z-20 border-2 border-transparent"
                    style={{
                      background: "linear-gradient(white, white) padding-box, conic-gradient(from var(--angle, 0deg), #38bdf8, #6366f1, #38bdf8) border-box",
                      animation: "spin-border 1.2s linear infinite",
                    }}
                  />
                </>
              )}
              <button
                onClick={() => handleGenerateArtifact("study_guide")}
                disabled={generatingArtifactType !== null}
                className={`relative z-30 w-full p-3 rounded-xl border text-left transition-all duration-200 space-y-1 shadow-xs group
                  ${generatingArtifactType === "study_guide"
                    ? "border-sky-400 bg-sky-50/80 dark:bg-sky-950/60 scale-[0.98] shadow-sky-200 dark:shadow-sky-900"
                    : generatingArtifactType !== null
                    ? "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 opacity-40 cursor-not-allowed"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 hover:bg-sky-50/50 dark:hover:bg-sky-950/30 hover:scale-[1.02]"
                  }`}
              >
                {generatingArtifactType === "study_guide"
                  ? <Loader2 className="w-4 h-4 text-sky-500 animate-spin" />
                  : <BookOpen className="w-4 h-4 text-sky-500 group-hover:scale-110 transition-transform" />
                }
                <div className={`text-xs font-semibold ${generatingArtifactType === "study_guide" ? "text-sky-600 dark:text-sky-400" : "text-slate-800 dark:text-slate-200 group-hover:text-sky-600"}`}>
                  {generatingArtifactType === "study_guide" ? "Generating…" : "Study Guide"}
                </div>
                <div className="text-[10px] text-slate-400">
                  {generatingArtifactType === "study_guide" ? "Building quiz & concepts" : "Quiz & key concepts"}
                </div>
              </button>
            </div>

            {/* Briefing Doc */}
            <div className="relative">
              {generatingArtifactType === "briefing_doc" && (
                <span className="absolute -inset-[2px] rounded-xl pointer-events-none z-10"
                  style={{
                    background: "conic-gradient(from var(--angle, 0deg), #10b981, #34d399, #10b981)",
                    animation: "spin-border 1.2s linear infinite",
                    borderRadius: "12px",
                    padding: "2px",
                  }}
                />
              )}
              <button
                onClick={() => handleGenerateArtifact("briefing_doc")}
                disabled={generatingArtifactType !== null}
                className={`relative z-30 w-full p-3 rounded-xl border text-left transition-all duration-200 space-y-1 shadow-xs group
                  ${generatingArtifactType === "briefing_doc"
                    ? "border-emerald-400 bg-emerald-50/80 dark:bg-emerald-950/60 scale-[0.98] shadow-emerald-200 dark:shadow-emerald-900"
                    : generatingArtifactType !== null
                    ? "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 opacity-40 cursor-not-allowed"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-emerald-500 hover:bg-emerald-50/50 dark:hover:bg-emerald-950/30 hover:scale-[1.02]"
                  }`}
              >
                {generatingArtifactType === "briefing_doc"
                  ? <Loader2 className="w-4 h-4 text-emerald-500 animate-spin" />
                  : <FileText className="w-4 h-4 text-emerald-500 group-hover:scale-110 transition-transform" />
                }
                <div className={`text-xs font-semibold ${generatingArtifactType === "briefing_doc" ? "text-emerald-600 dark:text-emerald-400" : "text-slate-800 dark:text-slate-200 group-hover:text-emerald-600"}`}>
                  {generatingArtifactType === "briefing_doc" ? "Generating…" : "Briefing Doc"}
                </div>
                <div className="text-[10px] text-slate-400">
                  {generatingArtifactType === "briefing_doc" ? "Extracting takeaways" : "Executive takeaways"}
                </div>
              </button>
            </div>

            {/* FAQ */}
            <div className="relative">
              {generatingArtifactType === "faq" && (
                <span className="absolute -inset-[2px] rounded-xl pointer-events-none z-10"
                  style={{
                    background: "conic-gradient(from var(--angle, 0deg), #f59e0b, #fbbf24, #f59e0b)",
                    animation: "spin-border 1.2s linear infinite",
                    borderRadius: "12px",
                    padding: "2px",
                  }}
                />
              )}
              <button
                onClick={() => handleGenerateArtifact("faq")}
                disabled={generatingArtifactType !== null}
                className={`relative z-30 w-full p-3 rounded-xl border text-left transition-all duration-200 space-y-1 shadow-xs group
                  ${generatingArtifactType === "faq"
                    ? "border-amber-400 bg-amber-50/80 dark:bg-amber-950/60 scale-[0.98] shadow-amber-200 dark:shadow-amber-900"
                    : generatingArtifactType !== null
                    ? "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 opacity-40 cursor-not-allowed"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-amber-500 hover:bg-amber-50/50 dark:hover:bg-amber-950/30 hover:scale-[1.02]"
                  }`}
              >
                {generatingArtifactType === "faq"
                  ? <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />
                  : <HelpCircle className="w-4 h-4 text-amber-500 group-hover:scale-110 transition-transform" />
                }
                <div className={`text-xs font-semibold ${generatingArtifactType === "faq" ? "text-amber-600 dark:text-amber-400" : "text-slate-800 dark:text-slate-200 group-hover:text-amber-600"}`}>
                  {generatingArtifactType === "faq" ? "Generating…" : "FAQ"}
                </div>
                <div className="text-[10px] text-slate-400">
                  {generatingArtifactType === "faq" ? "Forming questions" : "Top questions"}
                </div>
              </button>
            </div>

            {/* Timeline */}
            <div className="relative">
              {generatingArtifactType === "timeline" && (
                <span className="absolute -inset-[2px] rounded-xl pointer-events-none z-10"
                  style={{
                    background: "conic-gradient(from var(--angle, 0deg), #6366f1, #818cf8, #6366f1)",
                    animation: "spin-border 1.2s linear infinite",
                    borderRadius: "12px",
                    padding: "2px",
                  }}
                />
              )}
              <button
                onClick={() => handleGenerateArtifact("timeline")}
                disabled={generatingArtifactType !== null}
                className={`relative z-30 w-full p-3 rounded-xl border text-left transition-all duration-200 space-y-1 shadow-xs group
                  ${generatingArtifactType === "timeline"
                    ? "border-indigo-400 bg-indigo-50/80 dark:bg-indigo-950/60 scale-[0.98] shadow-indigo-200 dark:shadow-indigo-900"
                    : generatingArtifactType !== null
                    ? "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 opacity-40 cursor-not-allowed"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-500 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/30 hover:scale-[1.02]"
                  }`}
              >
                {generatingArtifactType === "timeline"
                  ? <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />
                  : <Clock className="w-4 h-4 text-indigo-500 group-hover:scale-110 transition-transform" />
                }
                <div className={`text-xs font-semibold ${generatingArtifactType === "timeline" ? "text-indigo-600 dark:text-indigo-400" : "text-slate-800 dark:text-slate-200 group-hover:text-indigo-600"}`}>
                  {generatingArtifactType === "timeline" ? "Generating…" : "Timeline"}
                </div>
                <div className="text-[10px] text-slate-400">
                  {generatingArtifactType === "timeline" ? "Ordering events" : "Chronological dates"}
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* =================================================================== */}
        {/* 3. NOTES BOARD                                                      */}
        {/* =================================================================== */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Notes & Pins ({notes.length})
            </span>
            <button
              onClick={() => setShowNewNoteModal(true)}
              className="text-[11px] text-sky-600 dark:text-sky-400 hover:underline flex items-center space-x-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add note</span>
            </button>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {notes.length === 0 ? (
              <div className="border border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-4 text-center text-[11px] text-slate-400">
                No notes saved yet. Pin chat responses or add custom notes here.
              </div>
            ) : (
              notes.map((note) => (
                <div
                  key={note.id}
                  className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5 shadow-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate pr-2">
                      {note.title}
                    </span>
                    <div className="flex items-center space-x-1 shrink-0">
                      <button
                        onClick={() => copyNoteText(note.id, note.content)}
                        className="p-1 text-slate-400 hover:text-slate-600 rounded"
                        title="Copy note"
                      >
                        {copiedId === note.id ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      </button>
                      <button
                        onClick={() => handleDeleteNote(note.id)}
                        className="p-1 text-slate-400 hover:text-rose-500 rounded"
                        title="Delete note"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-300 line-clamp-3 whitespace-pre-wrap">
                    {note.content}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Artifact Viewer Modal */}
      {activeArtifact && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col max-h-[85vh] overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950">
              <div className="flex items-center space-x-2">
                <Bookmark className="w-4 h-4 text-sky-500" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  {activeArtifact.title}
                </h3>
              </div>
              <button
                onClick={() => setActiveArtifact(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
              <ReactMarkdown
                components={{
                  h1: ({ node, ...props }) => <h1 className="text-base font-bold text-slate-900 dark:text-white pb-2 mb-3 border-b border-slate-200 dark:border-slate-800" {...props} />,
                  h2: ({ node, ...props }) => <h2 className="text-sm font-bold text-sky-600 dark:text-sky-400 mt-4 mb-2" {...props} />,
                  h3: ({ node, ...props }) => <h3 className="text-xs font-bold text-slate-900 dark:text-white mt-3 mb-1" {...props} />,
                  p: ({ node, ...props }) => <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed mb-2" {...props} />,
                  ul: ({ node, ...props }) => <ul className="list-disc pl-5 text-xs text-slate-700 dark:text-slate-300 space-y-1 my-2" {...props} />,
                  ol: ({ node, ...props }) => <ol className="list-decimal pl-5 text-xs text-slate-700 dark:text-slate-300 space-y-1 my-2" {...props} />,
                  li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
                  strong: ({ node, ...props }) => <strong className="font-semibold text-slate-900 dark:text-white" {...props} />,
                  hr: ({ node, ...props }) => <hr className="my-3 border-slate-200 dark:border-slate-800" {...props} />,
                  table: ({ node, ...props }) => <div className="overflow-x-auto my-3"><table className="min-w-full text-xs border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden" {...props} /></div>,
                  th: ({ node, ...props }) => <th className="bg-slate-100 dark:bg-slate-800/80 p-2 text-left font-semibold border-b border-slate-200 dark:border-slate-700" {...props} />,
                  td: ({ node, ...props }) => <td className="p-2 border-b border-slate-100 dark:border-slate-800/50" {...props} />,
                }}
              >
                {activeArtifact.content_markdown}
              </ReactMarkdown>
            </div>

            <div className="px-5 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex items-center justify-between text-xs">
              <span className="text-[11px] text-slate-400">
                Sources: {activeArtifact.sources_used.join(", ")}
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleSaveArtifactAsNote}
                  className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium"
                >
                  Save as Studio Note
                </button>
                <button
                  onClick={() => setActiveArtifact(null)}
                  className="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Custom Note Modal */}
      {showNewNoteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-sm w-full space-y-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">New Note Card</h3>
            <form onSubmit={handleCreateNote} className="space-y-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">Note Title</label>
                <input
                  type="text"
                  required
                  value={newNoteTitle}
                  onChange={(e) => setNewNoteTitle(e.target.value)}
                  placeholder="e.g. Contract Renewal Checklist"
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white mt-1"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">Note Content</label>
                <textarea
                  rows={4}
                  required
                  value={newNoteContent}
                  onChange={(e) => setNewNoteContent(e.target.value)}
                  placeholder="Key thoughts, notes or findings..."
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white mt-1"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewNoteModal(false)}
                  className="px-3 py-1.5 text-xs text-slate-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-medium"
                >
                  Save Note
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
