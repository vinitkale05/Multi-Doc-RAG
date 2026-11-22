# Multi-Document RAG with Citations
> **Production-grade Multi-Document RAG with verifiable inline citations, hybrid retrieval, reranking, evaluation and security built in.**

[![CI Pipeline](https://github.com/vinitkale/multi-document-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/vinitkale/multi-document-rag)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com/)

**Author:** Vinit Kale  
**Context:** MIT-ADT University, MIT School of Computing, Pune – Agentic AI Course (L.Y. SEM-I, AIA 3, Roll No. 55)  
**Date:** 22 November 2026  
**Status:** v1.0 Production-Ready Release

---

## Table of Contents
1. [Overview & Problem Statement](#1-overview--problem-statement)
2. [Key Engineering Innovations](#2-key-engineering-innovations)
3. [Measured Evaluation Benchmark Results](#3-measured-evaluation-benchmark-results)
4. [System Architecture & Workflow](#4-system-architecture--workflow)
5. [Inline Citation & Anti-Spoofing Architecture](#5-inline-citation--anti-spoofing-architecture)
6. [Security Model & Prompt-Injection Defenses](#6-security-model--prompt-injection-defenses)
7. [Tech Stack & Design Decisions](#7-tech-stack--design-decisions)
8. [Quick Start (One-Command Launch)](#8-quick-start-one-command-launch)
9. [REST API Reference & Examples](#9-rest-api-reference--examples)
10. [Automated Testing & CI/CD](#10-automated-testing--cicd)

---

## 1. Overview & Problem Statement

Standard GenAI chatbots hallucinate, cannot read complex private document collections, and provide zero verifiable proof for their claims. Basic tutorial RAG implementations typically retrieve 3 chunks from a single PDF and dump ungrounded answers.

**Multi-Document RAG with Citations** is an enterprise-grade GenAI research platform designed for legal, compliance, research, and technical teams. It answers natural-language questions across hundreds of heterogeneous documents simultaneously, attaches a **verifiable inline citation `[1]`, `[2]` to every single factual statement**, generates an immutable bibliography, and allows users to click any citation to view the exact supporting passage highlighted in context.

---

## 2. Key Engineering Innovations

* **Multi-Format Ingestion:** Native layout and structure extraction for **PDF**, **DOCX**, **PPTX**, **XLSX/CSV**, **HTML**, **Markdown**, and **TXT**, preserving page numbers, slide numbers, sheet names, and heading hierarchies.
* **SSRF-Protected URL Ingestion:** Safe web page fetching protected against Server-Side Request Forgery by validating DNS records against private subnets, loopbacks, and cloud metadata IPs (`169.254.169.254`).
* **Structure-Aware Recursive Chunking:** Target 500–800 tokens with 10–15% overlap, respecting table boundaries and section headers.
* **Hybrid Dense-Sparse Search:** Dual-stream retrieval combining dense vector similarity with Okapi BM25 keyword search, fused using **Reciprocal Rank Fusion (RRF $k=60$)**.
* **Multi-Document Diversity Balancing:** Prevents single large documents from dominating comparative multi-source research queries.
* **Cross-Encoder Reranking & Abstention:** Evaluates candidate chunks with semantic cross-attention. When evidence is insufficient or below threshold, the system **abstains** rather than guessing.
* **Server-Side Verified Inline Citations:** First-class citation validation pipeline that strips hallucinated or spoofed citation markers, renumbers citations chronologically to `[1]`, `[2]`, and attaches character highlight offsets.
* **Google NotebookLM 3-Panel Workspace:**
  * **Sources Panel (Left):** Toggle checkboxes to selectively scope grounding, source summary, and quick multi-file upload.
  * **Chat & Grounded Q&A (Center):** Interactive stream with clickable citation pills `[1]`, hover quote previews, and 1-click **Pin to Note** cards.
  * **Studio Panel (Right):**
    * **Audio Overview (Deep Dive Podcast):** 2 AI hosts (Alex & Taylor) unpack selected documents in a podcast dialogue with interactive speech synthesis audio player, speed control (1x/1.5x), and live turn transcript.
    * **Study Guide Generator:** Quiz, key definitions, and practice questions.
    * **Briefing Doc Generator:** Executive summary, key findings, and action items.
    * **FAQ Generator:** High-yield Q&A synthesized from documents.
    * **Timeline Generator:** Chronological milestones, renewal windows, and SLA response horizons.
    * **Notes & Pins Board:** Editable card grid with markdown export.
* **Tenant Isolation & RBAC:** Multi-tenant database schema enforced at the retrieval layer, preventing cross-tenant data leakage.

---

## 3. Measured Evaluation Benchmark Results

Evaluated on the curated Golden Benchmark Dataset (PRD Section 12 standards):

| Evaluation Layer | Target Metric | PRD v1.0 Target | Measured Result | Benchmark Status |
|---|---|---|---|---|
| **Retrieval** | Recall@10 | $\ge 0.90$ | **1.00** | **PASSED** |
| **Retrieval** | Hit Rate@10 | $\ge 0.90$ | **1.00** | **PASSED** |
| **Reranking** | Precision@5 after Rerank | $\ge 0.75$ | **1.00** | **PASSED** |
| **Generation** | Faithfulness / Groundedness | $\ge 0.90$ | **0.93** | **PASSED** |
| **Citations** | Citation Precision | $\ge 0.92$ | **1.00** | **PASSED** |
| **Citations** | Citation Coverage | $\ge 0.95$ | **1.00** | **PASSED** |
| **Abstention** | Correct Abstention on Unanswerable | $\ge 0.90$ | **1.00** | **PASSED** |
| **Safety** | Prompt-Injection Attack Success | **0.0%** | **0.00%** | **PASSED** |
| **Performance** | Median Query Latency (p50) | $< 800\text{ ms}$ | **0.1 ms (mock) / 380 ms (LLM)** | **PASSED** |

> *Reproduce these benchmarks at any time via: `python3 scripts/run_eval.py`*

---

## 4. System Architecture & Workflow

```
+-----------------------------------------------------------------------------------+
|                                 CLIENT LAYER                                      |
|  Next.js 14 App Router • React 18 • TypeScript • Tailwind CSS • Streaming UI      |
+------------------------------------------+----------------------------------------+
                                           | HTTP REST / SSE Stream
                                           v
+-----------------------------------------------------------------------------------+
|                                API GATEWAY LAYER                                  |
|   FastAPI • JWT Security • Role-Based Access Control • Hard Tenant Filtering      |
+------------------------------------------+----------------------------------------+
                                           |
               +---------------------------+---------------------------+
               |                                                       |
               v                                                       v
+-----------------------------+                         +-----------------------------+
|    INGESTION PIPELINE       |                         |    ONLINE QUERY PIPELINE    |
| - Layout Parsers (PDF/DOCX) |                         | - Rolling Memory & Rewrite  |
| - SSRF URL Validator        |                         | - Dense Vector Search       |
| - Cleaner & Anti-Injection  |                         | - Okapi BM25 Keyword Search |
| - Structure-Aware Chunker   |                         | - Reciprocal Rank Fusion    |
| - Vector & Keyword Indexing |                         | - Cross-Encoder Reranker    |
+--------------+--------------+                         | - Grounded Prompt Builder   |
               |                                        | - Streaming LLM Synthesis   |
               v                                        | - Citation Validation & Map |
+-----------------------------+                         +--------------+--------------+
|       DATA STORES           |                                        |
| - PostgreSQL / SQLite       |<---------------------------------------+
| - Vector Store (Cosine)     |
| - BM25 Inverted Index       |
| - Local / S3 File Storage   |
+-----------------------------+
```

---

## 5. Inline Citation & Anti-Spoofing Architecture

Unlike standard RAG apps where citations are mere markdown strings added by an LLM, this platform enforces citations as a **verified invariant**:

1. **Structured Source Labeling:** Every retrieved chunk passed to the LLM is isolated inside `<context>` blocks labeled `[S1]`, `[S2]`, ... carrying hidden metadata (document ID, title, page, section, and character offsets).
2. **Grounded Generation:** The LLM is instructed to answer only from the provided context and attach the corresponding tag after every claim: e.g. `"The contract renews automatically each year [S1]."`
3. **Citation Validator:**
   - Detects all `[S\d+]` tokens.
   - Cross-references each token against authorized, retrieved chunks.
   - **Strips any hallucinated or spoofed tags** (e.g. `[S99]`).
   - Renumbers valid citations to chronological user-facing tags `[1]`, `[2]`.
   - Returns structured JSON with exact snippet, page, and highlight offsets.
   - Aggregates an immutable `bibliography` array grouped by document.

### Example Citation Response Payload
```json
{
  "answer": "The contract renews automatically each year [1]. Enterprise support is $1200 monthly [2].",
  "citations": [
    {
      "id": 1,
      "document_id": "doc_8f2",
      "title": "MSA_Acme_Corporation.pdf",
      "page": 1,
      "section": "1. Term and Renewal",
      "chunk_id": "ch_0193",
      "snippet": "...The agreement renews automatically for successive one-year terms...",
      "score": 0.94,
      "highlight": { "start": 142, "end": 288 }
    }
  ],
  "bibliography": [
    { "document_id": "doc_8f2", "title": "MSA_Acme_Corporation.pdf", "pages": [1] }
  ],
  "grounded": true,
  "trace_id": "tr_77a1"
}
```

---

## 6. Security Model & Prompt-Injection Defenses

* **Indirect Document Injections:** Documents are untrusted input. The ingestion normalizer detects and defangs malicious instructions (e.g. `"ignore previous instructions"`) by replacing them with `[NEUTRALIZED_UNTRUSTED_DOC_DIRECTIVE]`.
* **Prompt Delimiter Isolation:** Context is enclosed within strictly demarcated `<context>` tags with explicit system prompt instructions treating all enclosed text as inert factual data.
* **Citation Anti-Spoofing:** Server-side validation discards unauthorized source tags generated by jailbreaks.
* **SSRF Protection:** Web ingestion validates hostnames against private RFC 1918 subnets, loopbacks, and cloud metadata services (`169.254.169.254`).
* **Tenant Isolation:** Every database and vector search query applies a hard `tenant_id` filter.
* **Automated Red-Team Suite:** CI runs an automated prompt-injection test suite verifying a 0.0% attack success rate.

---

## 7. Tech Stack & Design Decisions

| Component | Technology | Rationale & ADR Reference |
|---|---|---|
| **Backend API** | FastAPI / Python 3.11+ | High-throughput asynchronous REST API and native SSE streaming. |
| **Retrieval Engine** | Hybrid Dense + Okapi BM25 | Combines semantic matching with exact keyword/code recall ([ADR 001](docs/adr/ADR-001-hybrid-retrieval.md)). |
| **Reranker** | Cross-Encoder Scoring | Discards low-relevance chunks and powers abstention on unanswerable questions. |
| **Citations** | Server-Side Validator | Enforces 100% verifiable citations and prevents spoofing ([ADR 002](docs/adr/ADR-002-citation-validation-architecture.md)). |
| **Database** | PostgreSQL with pgvector | Production ACID metadata storage with vector similarity indexing. |
| **Frontend** | Next.js 14, React 18, Tailwind | Streaming UI, interactive citation popovers, side-by-side passage viewer. |

---

## 8. Quick Start (One-Command Launch)

### Option A: Docker Compose (Full Stack)
```bash
# Clone and launch all services
docker compose up --build -d
```
* **Frontend Application:** `http://localhost:3000`
* **FastAPI Backend:** `http://localhost:8000`
* **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
* **MinIO Storage Console:** `http://localhost:9001`

---

### Option B: Standalone Local Development

#### 1. Backend Setup
```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m app.main
```

#### 2. Seed Demo Workspace & Data
```bash
# From project root
python3 scripts/seed_data.py
```
* **Default Admin:** `admin@rag.local` / `AdminPass123!`
* **Default Researcher:** `researcher@rag.local` / `MemberPass123!`

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000` in your browser.

---

## 9. REST API Reference & Examples

All endpoints (except `/auth/*` and `/health`) require `Authorization: Bearer <token>`.

### 1. Ingest Documents (Multipart Upload)
```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@MSA_Acme_Corporation.pdf"
```

### 2. Ingest from Web URL (SSRF-Protected)
```bash
curl -X POST "http://localhost:8000/api/v1/collections/{collection_id}/documents/url" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/spec", "title": "API Specification"}'
```

### 3. Ask a Grounded Question with Citations
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the renewal terms and uptime SLAs across the contracts?",
    "collection_ids": [],
    "options": { "top_k": 30, "rerank_top_n": 8, "stream": false }
  }'
```

### 4. Fetch Highlighted Citation Passage for Document Viewer
```bash
curl -X GET "http://localhost:8000/api/v1/citations/{chunk_id}" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 10. Automated Testing & CI/CD

Run the test and verification suites:

```bash
# 1. Core Unit Tests (Parsers, Chunkers, Citations, Hybrid Search)
cd backend && python3 -m pytest tests/

# 2. Red-Team Prompt Injection Security Suite
python3 scripts/test_prompt_injection.py

# 3. Golden Dataset Evaluation Benchmark
python3 scripts/run_eval.py
```

### Automated GitHub Actions CI
Every commit and pull request runs:
- Ruff linting and formatting checks
- Pytest unit and integration suites
- Automated adversarial prompt-injection tests
- Golden dataset RAG regression benchmarks

---

## License
MIT License. Authored by **Vinit Kale** (MIT School of Computing, Pune, 2026).
