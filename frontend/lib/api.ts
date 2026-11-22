import { Collection, DocumentItem, Conversation, Message, CitationPassageInfo } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("rag_access_token");
  }
  return null;
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("rag_access_token", token);
  }
}

export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("rag_access_token");
  }
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers = { ...authHeaders(), ...(options.headers || {}) };
  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined" && !window.location.pathname.includes("/auth")) {
      window.location.href = "/auth/login";
    }
  }

  if (!res.ok) {
    let errDetail = "API Request failed";
    try {
      const errJson = await res.json();
      errDetail = errJson.message || errJson.detail || JSON.stringify(errJson);
    } catch {
      errDetail = res.statusText;
    }
    throw new Error(errDetail);
  }

  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

// Authentication API
export async function loginApi(email: string, password: string) {
  const data = await apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function registerApi(email: string, password: string, tenantName: string) {
  const data = await apiFetch<{ access_token: string; refresh_token: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, tenant_name: tenantName, role: "admin" }),
  });
  setToken(data.access_token);
  return data;
}

export async function getMeApi() {
  return apiFetch<{ id: string; email: string; role: string; tenant_id: string }>("/me");
}

// Collections API
export async function getCollectionsApi(): Promise<Collection[]> {
  return apiFetch<Collection[]>("/collections");
}

export async function createCollectionApi(name: string, description: string): Promise<Collection> {
  return apiFetch<Collection>("/collections", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });
}

export async function deleteCollectionApi(id: string): Promise<void> {
  return apiFetch<void>(`/collections/${id}`, { method: "DELETE" });
}

// Documents API
export async function getDocumentsApi(collectionId: string): Promise<DocumentItem[]> {
  return apiFetch<DocumentItem[]>(`/collections/${collectionId}/documents`);
}

export async function uploadDocumentsApi(collectionId: string, files: File[]): Promise<DocumentItem[]> {
  const token = getToken();
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const res = await fetch(`${API_BASE}/collections/${collectionId}/documents`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function ingestUrlApi(collectionId: string, url: string, title?: string): Promise<DocumentItem> {
  return apiFetch<DocumentItem>(`/collections/${collectionId}/documents/url`, {
    method: "POST",
    body: JSON.stringify({ url, title }),
  });
}

export async function deleteDocumentApi(documentId: string): Promise<void> {
  return apiFetch<void>(`/documents/${documentId}`, { method: "DELETE" });
}

export async function retryDocumentApi(documentId: string): Promise<DocumentItem> {
  return apiFetch<DocumentItem>(`/documents/${documentId}/retry`, { method: "POST" });
}

// Citations API
export async function getCitationPassageApi(chunkId: string): Promise<CitationPassageInfo> {
  return apiFetch<CitationPassageInfo>(`/citations/${chunkId}`);
}

// NotebookLM Studio & Notes API
export async function generateAudioOverviewApi(documentIds: string[], collectionId?: string) {
  return apiFetch<any>("/notebook/audio-overview", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds, collection_id: collectionId }),
  });
}

export async function generateStudyGuideApi(documentIds: string[], collectionId?: string) {
  return apiFetch<any>("/notebook/study-guide", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds, collection_id: collectionId }),
  });
}

export async function generateBriefingDocApi(documentIds: string[], collectionId?: string) {
  return apiFetch<any>("/notebook/briefing-doc", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds, collection_id: collectionId }),
  });
}

export async function generateFaqApi(documentIds: string[], collectionId?: string) {
  return apiFetch<any>("/notebook/faq", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds, collection_id: collectionId }),
  });
}

export async function generateTimelineApi(documentIds: string[], collectionId?: string) {
  return apiFetch<any>("/notebook/timeline", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds, collection_id: collectionId }),
  });
}

export async function getNotesApi() {
  return apiFetch<any[]>("/notebook/notes");
}

export async function createNoteApi(title: string, content: string, noteType = "user_note", collectionId?: string) {
  return apiFetch<any>("/notebook/notes", {
    method: "POST",
    body: JSON.stringify({ title, content, note_type: noteType, collection_id: collectionId }),
  });
}

export async function deleteNoteApi(noteId: string) {
  return apiFetch<void>(`/notebook/notes/${noteId}`, { method: "DELETE" });
}

// Feedback API
export async function submitFeedbackApi(messageId: string, rating: number, reason?: string) {
  return apiFetch(`/messages/${messageId}/feedback`, {
    method: "POST",
    body: JSON.stringify({ rating, reason }),
  });
}

// Chat API (Streaming SSE)
export async function streamChatApi({
  question,
  conversationId,
  collectionIds,
  documentIds,
  onToken,
  onResult,
  onError,
}: {
  question: string;
  conversationId?: string;
  collectionIds?: string[];
  documentIds?: string[];
  onToken: (token: string) => void;
  onResult: (result: any) => void;
  onError: (err: Error) => void;
}) {
  const token = getToken();
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        question,
        conversation_id: conversationId,
        collection_ids: collectionIds || [],
        document_ids: documentIds || [],
        options: { stream: true, top_k: 30, rerank_top_n: 8 },
      }),
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail?.message || errJson.detail || "Chat request failed");
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("Response body is not readable");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const block of lines) {
        if (!block.trim()) continue;
        const eventMatch = block.match(/^event:\s*(\w+)/m);
        const dataMatch = block.match(/^data:\s*(.+)$/m);

        const eventType = eventMatch ? eventMatch[1] : "message";
        const dataStr = dataMatch ? dataMatch[1] : "";

        if (eventType === "token") {
          try {
            const parsed = JSON.parse(dataStr);
            onToken(parsed.token);
          } catch {
            onToken(dataStr);
          }
        } else if (eventType === "result") {
          try {
            const resultData = JSON.parse(dataStr);
            onResult(resultData);
          } catch (e) {
            console.error("Error parsing result payload", e);
          }
        }
      }
    }
  } catch (err: any) {
    onError(err);
  }
}
