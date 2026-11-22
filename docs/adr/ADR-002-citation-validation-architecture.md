# ADR 002: Server-Side Citation Validation and Anti-Spoofing Architecture

## Status
Accepted

## Context
Standard RAG systems either ask LLMs to format citations as plain text at the end of answers (which are frequently hallucinated or misattributed), or treat citation markers as purely decorative markdown without verification. Furthermore, malicious documents can contain adversarial text that mimics citation formatting or attempts to spoof sources.

## Decision
1. Citations are treated as a first-class, verified invariant structured data type.
2. The LLM is provided structured, isolated `<context>` blocks labeled `[S1]`, `[S2]`, ...
3. After streaming / generating text, the server-side `CitationValidator`:
   - Scans output text for all `[S\d+]` tokens.
   - Verifies whether each token maps to a chunk that was authorized and provided in the prompt context.
   - Completely removes any hallucinated or spoofed citation markers.
   - Renumbers valid citations to chronological order `[1]`, `[2]`, `[3]`.
   - Attaches chunk metadata (document ID, title, page start/end, section path, and char highlight offsets).
   - Generates an immutable bibliography payload.

## Consequences
- Guaranteed 100% citation precision against provided chunks.
- Prevents LLM citation spoofing attacks.
- Frontend can reliably provide interactive click-to-highlight navigation into original source documents.
