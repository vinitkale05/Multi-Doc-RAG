# PRODUCT REQUIREMENTS DOCUMENT
## Multi-Document RAG with Citations
### A production-ready GenAI platform for grounded question answering across many documents, with verifiable inline citations

| Field | Detail |
|---|---|
| Product | Multi-Document RAG with Citations |
| Document type | Product Requirements Document (PRD) |
| Version / status | v1.0 – Production Spec |
| Author | Vinit Kale |
| Context | MIT-ADT University, MIT School of Computing, Pune – Agentic AI course (L.Y. SEM-I, AIA 3, Roll No. 55) |
| Date | 22 November 2026 |
| Positioning | Portfolio-grade, production-style GenAI system (not a basic PDF chatbot) |

---

## 1. Product Vision & Problem Statement
Give every user a trustworthy research assistant that reads their entire document collection, answers questions in natural language, and proves every claim by pointing to the exact passage it came from. The product makes it faster to find answers and just as easy to verify them.

## 2. Key Architecture Pillars
1. Multi-format ingestion (PDF, DOCX, PPTX, XLSX/CSV, HTML, TXT) with SSRF protection.
2. Structure-aware recursive chunking (500–800 tokens, 10–15% overlap) preserving page, slide, and heading metadata.
3. Hybrid Retrieval: Dense cosine embeddings + BM25 keyword search fused via Reciprocal Rank Fusion (RRF $k=60$).
4. Cross-Encoder reranking with score thresholding and strict abstention when evidence is insufficient.
5. First-class inline citation architecture: server-side validation, anti-spoofing, renumbering `[1]`, `[2]`, snippet generation, char highlight offsets, and bibliography.
6. Tenant isolation and red-team prompt injection protection.
7. Automated evaluation harness benchmarked against golden test dataset.
