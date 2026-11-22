import pytest
from app.services.citations.validator import citation_validator
from app.services.retrieval.reranker import ScoredChunk
from app.services.retrieval.hybrid import HybridRetrievedChunk


def make_mock_scored_chunk(chunk_id: str, doc_id: str, title: str, text: str, page: int = 1) -> ScoredChunk:
    chunk = HybridRetrievedChunk(
        chunk_id=chunk_id,
        rrf_score=0.9,
        text=text,
        metadata={
            "document_id": doc_id,
            "filename": title,
            "page_start": page,
            "section_path": "Terms",
            "char_start": 0,
            "char_end": len(text)
        }
    )
    return ScoredChunk(chunk=chunk, rerank_score=0.92)


def test_citation_validation_and_renumbering():
    source_map = {
        "S1": make_mock_scored_chunk("c1", "doc_a", "MSA_Acme.pdf", "The contract renews automatically each year."),
        "S2": make_mock_scored_chunk("c2", "doc_b", "Pricing_Beta.pdf", "Enterprise plan costs $500 monthly.", page=3)
    }

    raw_answer = "Revenue increased and renewal is annual [S1]. Support cost is $500 monthly [S2]."
    result = citation_validator.validate_and_renumber(raw_answer, source_map)

    # Renumbered to [1] and [2]
    assert "[1]" in result.cleaned_answer
    assert "[2]" in result.cleaned_answer
    assert "[S1]" not in result.cleaned_answer
    assert len(result.citations) == 2
    assert result.citations[0].id == 1
    assert result.citations[0].title == "MSA_Acme.pdf"
    assert result.citations[1].id == 2
    assert result.citations[1].page == 3
    assert len(result.bibliography) == 2
    assert result.grounded is True
    assert result.citation_precision == 1.0


def test_citation_spoofing_rejected():
    source_map = {
        "S1": make_mock_scored_chunk("c1", "doc_a", "Doc1.pdf", "Only S1 exists.")
    }

    # Model hallucinates citation [S99] which wasn't provided
    raw_answer = "Verified statement [S1]. Fake statement hallucinated by model [S99]."
    result = citation_validator.validate_and_renumber(raw_answer, source_map)

    # S99 should be stripped out
    assert "[S99]" not in result.cleaned_answer
    assert "[1]" in result.cleaned_answer
    assert len(result.citations) == 1
    # Precision should reflect 1 valid out of 2 total
    assert result.citation_precision == 0.5
