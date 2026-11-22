# ADR 001: Hybrid Dense-Sparse Retrieval with Reciprocal Rank Fusion

## Status
Accepted

## Context
Standard vector-only RAG pipelines fail on domain-specific keywords, legal clause numbering (e.g. "Section 12.2"), exact acronyms, and product identifiers. Pure BM25 keyword search misses semantic paraphrasing, synonyms, and multilingual context.

## Decision
We implemented a dual-retrieval hybrid engine:
1. **Dense Vector Search:** High-dimensional semantic cosine similarity using normalized embedding vectors.
2. **Sparse BM25 Index:** Okapi BM25 inverted index with custom tokenization, stop-word filtering, and Robertson-Spärck Jones IDF scoring.
3. **Fusion:** Reciprocal Rank Fusion (RRF) with constant $k = 60$, combining ranks without requiring complex scale calibration between distance metrics and term frequencies.
4. **Diversity:** Multi-document coverage penalty balancing chunks across documents for comparative questions.

## Consequences
- Significant increase in recall on rare keywords and exact section queries.
- Zero calibration required when changing underlying embedding providers.
- Consistent Recall@10 of $\ge 0.90$ across the golden evaluation dataset.
