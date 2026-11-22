import re
from typing import List, Dict, Any, Tuple
from app.services.retrieval.reranker import ScoredChunk
from app.schemas import CitationDetail, BibliographyItem, CitationHighlight


class ValidatedCitationsResult:
    def __init__(
        self,
        cleaned_answer: str,
        citations: List[CitationDetail],
        bibliography: List[BibliographyItem],
        grounded: bool,
        citation_precision: float,
        citation_coverage: float
    ):
        self.cleaned_answer = cleaned_answer
        self.citations = citations
        self.bibliography = bibliography
        self.grounded = grounded
        self.citation_precision = citation_precision
        self.citation_coverage = citation_coverage


class CitationValidator:
    def validate_and_renumber(
        self,
        raw_answer: str,
        source_map: Dict[str, ScoredChunk]
    ) -> ValidatedCitationsResult:
        """Parses [S1], [S2] markers from the LLM output, validates them against supplied context,

        rejects spoofed IDs, renumbers in order of first appearance to [1], [2],
        and constructs citation payloads and bibliography.
        """
        if not raw_answer:
            return ValidatedCitationsResult(
                cleaned_answer="",
                citations=[],
                bibliography=[],
                grounded=False,
                citation_precision=0.0,
                citation_coverage=0.0,
            )

        # Pattern to capture [S1], [S2], [S12], etc.
        source_tag_pattern = re.compile(r"\[(S\d+)\]")

        # Find all cited source IDs
        found_tags = source_tag_pattern.findall(raw_answer)

        # Track valid and invalid
        valid_found = []
        invalid_found = []
        for tag in found_tags:
            if tag in source_map:
                valid_found.append(tag)
            else:
                invalid_found.append(tag)

        # Mapping from source tag (e.g. 'S3') to user-facing integer ID (1, 2, ...)
        tag_to_user_id: Dict[str, int] = {}
        citations_list: List[CitationDetail] = []
        user_counter = 1

        for tag in valid_found:
            if tag not in tag_to_user_id:
                tag_to_user_id[tag] = user_counter
                scored = source_map[tag]
                meta = scored.chunk.metadata

                # Extract concise snippet
                chunk_text = scored.chunk.text.strip()
                snippet = chunk_text[:200] + ("..." if len(chunk_text) > 200 else "")

                citation = CitationDetail(
                    id=user_counter,
                    document_id=str(meta.get("document_id", "")),
                    title=str(meta.get("filename", "Source Document")),
                    page=int(meta.get("page_start", 1)),
                    section=str(meta.get("section_path", "")),
                    chunk_id=str(scored.chunk.chunk_id),
                    snippet=snippet,
                    score=round(scored.rerank_score, 3),
                    highlight=CitationHighlight(
                        start=int(meta.get("char_start", 0)),
                        end=int(meta.get("char_end", len(chunk_text)))
                    )
                )
                citations_list.append(citation)
                user_counter += 1

        # Replace in answer text: replace invalid tags with empty, valid tags with user-facing [1]
        def replace_tag(match):
            tag = match.group(1)
            if tag in tag_to_user_id:
                return f"[{tag_to_user_id[tag]}]"
            return ""  # Remove spoofed/invalid citation

        cleaned_text = source_tag_pattern.sub(replace_tag, raw_answer)

        # Clean up any doubled spaces or orphan punctuation resulting from tag removals
        cleaned_text = re.sub(r"\s+([.,;:!?])", r"\1", cleaned_text)
        cleaned_text = re.sub(r"\[\s*\]", "", cleaned_text)

        # Build bibliography grouped by document
        doc_pages_map: Dict[str, Tuple[str, set]] = {}
        for c in citations_list:
            if c.document_id not in doc_pages_map:
                doc_pages_map[c.document_id] = (c.title, set())
            doc_pages_map[c.document_id][1].add(c.page)

        bibliography: List[BibliographyItem] = [
            BibliographyItem(
                document_id=doc_id,
                title=title,
                pages=sorted(list(pages))
            )
            for doc_id, (title, pages) in doc_pages_map.items()
        ]

        # Calculate metrics
        total_citations = len(found_tags)
        citation_precision = (len(valid_found) / total_citations) if total_citations > 0 else 1.0

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned_text) if len(s.strip()) > 15]
        cited_sentences = sum(1 for s in sentences if re.search(r"\[\d+\]", s))
        citation_coverage = (cited_sentences / len(sentences)) if sentences else 1.0

        grounded = len(citations_list) > 0 or "insufficient evidence" in cleaned_text.lower()

        return ValidatedCitationsResult(
            cleaned_answer=cleaned_text.strip(),
            citations=citations_list,
            bibliography=bibliography,
            grounded=grounded,
            citation_precision=round(citation_precision, 3),
            citation_coverage=round(citation_coverage, 3)
        )


citation_validator = CitationValidator()
