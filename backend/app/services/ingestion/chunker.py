import hashlib
import re
import uuid
from typing import List, Dict, Any, Optional
from app.services.ingestion.parsers import ParsedPage


class ChunkItem:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        ordinal: int,
        text: str,
        page_start: int,
        page_end: int,
        section_path: str,
        char_start: int,
        char_end: int,
        token_count: int,
        content_hash: str
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.ordinal = ordinal
        self.text = text
        self.page_start = page_start
        self.page_end = page_end
        self.section_path = section_path
        self.char_start = char_start
        self.char_end = char_end
        self.token_count = token_count
        self.content_hash = content_hash


def estimate_tokens(text: str) -> int:
    # A reliable rule of thumb: ~4 characters per token in English text
    return max(1, len(text) // 4)


class StructureAwareChunker:
    """Structure-aware recursive chunker that respects headings, tables, paragraphs, and sentences."""

    def __init__(self, target_tokens: int = 700, overlap_tokens: int = 100):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.target_chars = target_tokens * 4
        self.overlap_chars = overlap_tokens * 4

    def chunk_pages(self, pages: List[ParsedPage], document_id: str) -> List[ChunkItem]:
        chunks: List[ChunkItem] = []
        ordinal = 0
        global_char_offset = 0

        current_section = "Introduction"

        for page in pages:
            page_text = page.text
            if not page_text.strip():
                continue

            # Update section path if headings present
            if page.headings:
                current_section = " > ".join(page.headings[:2])

            # Split primarily on paragraphs or table blocks
            paragraphs = re.split(r"\n{2,}", page_text)
            buffer = ""
            buffer_start_offset = global_char_offset

            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue

                if len(buffer) + len(p) <= self.target_chars:
                    if buffer:
                        buffer += "\n\n" + p
                    else:
                        buffer = p
                else:
                    # If buffer is already substantial, flush it
                    if buffer:
                        chunk_text = buffer.strip()
                        c_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                        chunk_id = str(uuid.uuid4())
                        chunks.append(
                            ChunkItem(
                                chunk_id=chunk_id,
                                document_id=document_id,
                                ordinal=ordinal,
                                text=chunk_text,
                                page_start=page.page_number,
                                page_end=page.page_number,
                                section_path=current_section,
                                char_start=buffer_start_offset,
                                char_end=buffer_start_offset + len(chunk_text),
                                token_count=estimate_tokens(chunk_text),
                                content_hash=c_hash,
                            )
                        )
                        ordinal += 1

                        # Compute overlap from end of buffer
                        overlap_slice = buffer[-self.overlap_chars:] if len(buffer) > self.overlap_chars else ""
                        buffer = (overlap_slice + "\n\n" + p).strip() if overlap_slice else p
                        buffer_start_offset = global_char_offset + len(chunk_text) - len(overlap_slice)
                    else:
                        # Paragraph itself is larger than target_chars: split by sentence
                        sentences = re.split(r"(?<=[.!?])\s+", p)
                        sentence_buf = ""
                        for sent in sentences:
                            if len(sentence_buf) + len(sent) <= self.target_chars:
                                sentence_buf += (" " if sentence_buf else "") + sent
                            else:
                                if sentence_buf:
                                    c_hash = hashlib.sha256(sentence_buf.encode("utf-8")).hexdigest()
                                    chunks.append(
                                        ChunkItem(
                                            chunk_id=str(uuid.uuid4()),
                                            document_id=document_id,
                                            ordinal=ordinal,
                                            text=sentence_buf.strip(),
                                            page_start=page.page_number,
                                            page_end=page.page_number,
                                            section_path=current_section,
                                            char_start=buffer_start_offset,
                                            char_end=buffer_start_offset + len(sentence_buf),
                                            token_count=estimate_tokens(sentence_buf),
                                            content_hash=c_hash,
                                        )
                                    )
                                    ordinal += 1
                                sentence_buf = sent
                        buffer = sentence_buf

            # Flush remaining buffer from this page
            if buffer.strip():
                chunk_text = buffer.strip()
                c_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                chunks.append(
                    ChunkItem(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        ordinal=ordinal,
                        text=chunk_text,
                        page_start=page.page_number,
                        page_end=page.page_number,
                        section_path=current_section,
                        char_start=buffer_start_offset,
                        char_end=buffer_start_offset + len(chunk_text),
                        token_count=estimate_tokens(chunk_text),
                        content_hash=c_hash,
                    )
                )
                ordinal += 1

            global_char_offset += len(page_text)

        return chunks
