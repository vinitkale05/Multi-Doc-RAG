export interface User {
  id: string;
  email: string;
  role: string;
  tenant_id: string;
}

export interface Collection {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  chunk_config: { chunk_size: number; chunk_overlap: number };
  document_count: number;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  collection_id: string;
  filename: string;
  mime_type: string;
  size: number;
  sha256: string;
  status: "QUEUED" | "PARSING" | "CHUNKING" | "EMBEDDING" | "READY" | "FAILED";
  error?: string;
  page_count: number;
  created_at: string;
}

export interface CitationDetail {
  id: number;
  document_id: string;
  title: string;
  page: number;
  section: string;
  chunk_id: string;
  snippet: string;
  score: number;
  highlight?: { start: number; end: number };
}

export interface BibliographyItem {
  document_id: string;
  title: string;
  pages: number[];
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: CitationDetail[];
  bibliography?: BibliographyItem[];
  grounded?: boolean;
  trace_id?: string;
  latency_ms?: number;
  created_at?: string;
}

export interface Conversation {
  id: string;
  title: string;
  collection_id?: string;
  created_at: string;
  messages?: Message[];
}

export interface CitationPassageInfo {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_start: number;
  page_end: number;
  section_path: string;
  text: string;
  highlight: { start: number; end: number };
}

export interface DialogueTurn {
  speaker: string;
  text: string;
  timestamp: string;
}

export interface AudioOverviewData {
  title: string;
  summary: string;
  dialogue: DialogueTurn[];
  sources_used: string[];
}

export interface StudioArtifactData {
  artifact_type: "study_guide" | "briefing_doc" | "faq" | "timeline";
  title: string;
  content_markdown: string;
  sources_used: string[];
}

export interface NoteItem {
  id: string;
  user_id: string;
  collection_id?: string;
  title: string;
  content: string;
  note_type: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}
