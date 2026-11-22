import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Patterns commonly used in indirect prompt injection in documents
SUSPICIOUS_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior)\s+directives?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|unrestricted|DAN)", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*override", re.IGNORECASE),
    re.compile(r"<\s*script.*?>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*iframe.*?>.*?<\s*/\s*iframe\s*>", re.IGNORECASE | re.DOTALL),
]


def normalize_text(text: str) -> str:
    """Normalize unicode and line endings."""
    if not text:
        return ""
    # Normalize unicode to NFKC
    normalized = unicodedata.normalize("NFKC", text)
    # Standardize line breaks
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    # Remove null bytes and non-printable control chars except tabs and newlines
    normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", normalized)
    # Collapse 3+ consecutive newlines into 2
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def sanitize_document_text(text: str) -> tuple[str, bool]:
    """Clean text and defang suspicious prompt injection triggers while preserving content."""
    cleaned = normalize_text(text)
    injection_found = False

    for pattern in SUSPICIOUS_INJECTION_PATTERNS:
        if pattern.search(cleaned):
            injection_found = True
            logger.warning(f"Detected suspicious indirect injection pattern matching {pattern.pattern} - neutralising.")
            # Neutralize by replacing with safe neutralized placeholder
            cleaned = pattern.sub("[NEUTRALIZED_UNTRUSTED_DOC_DIRECTIVE]", cleaned)

    return cleaned, injection_found
