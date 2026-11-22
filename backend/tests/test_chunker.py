import pytest
from app.services.ingestion.parsers import ParsedPage
from app.services.ingestion.chunker import StructureAwareChunker, estimate_tokens


def test_chunker_basic_split():
    chunker = StructureAwareChunker(target_tokens=50, overlap_tokens=10)
    text = "Paragraph one with some text. " * 10 + "\n\n" + "Paragraph two with more details. " * 10
    pages = [ParsedPage(page_number=1, text=text, headings=["Overview"])]

    chunks = chunker.chunk_pages(pages, document_id="doc_123")
    assert len(chunks) >= 2
    for c in chunks:
        assert c.document_id == "doc_123"
        assert c.page_start == 1
        assert c.section_path == "Overview"
        assert c.token_count > 0
        assert len(c.content_hash) == 64


def test_chunker_preserves_section_hierarchy():
    chunker = StructureAwareChunker(target_tokens=100, overlap_tokens=20)
    page1 = ParsedPage(page_number=1, text="Contract terms and conditions.\nRenewal happens yearly.", headings=["Section 1", "Renewal"])
    page2 = ParsedPage(page_number=2, text="Pricing schedule and SLA details.\n99.9% uptime guaranteed.", headings=["Section 2", "SLA"])

    chunks = chunker.chunk_pages([page1, page2], document_id="doc_multi")
    assert len(chunks) == 2
    assert "Section 1" in chunks[0].section_path
    assert "Section 2" in chunks[1].section_path
    assert chunks[0].page_start == 1
    assert chunks[1].page_start == 2
