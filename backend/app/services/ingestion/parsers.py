import io
import re
from typing import List, Dict, Any, Tuple
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup


class ParsedPage:
    def __init__(self, page_number: int, text: str, tables: List[str] = None, headings: List[str] = None):
        self.page_number = page_number
        self.text = text
        self.tables = tables or []
        self.headings = headings or []


class BaseDocumentParser(ABC):
    @abstractmethod
    def parse(self, content_bytes: bytes, filename: str) -> List[ParsedPage]:
        pass


class PDFParser(BaseDocumentParser):
    def parse(self, content_bytes: bytes, filename: str) -> List[ParsedPage]:
        pages = []
        errors = []

        # Strategy 1: pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes), strict=False)
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                headings = [
                    line.strip()
                    for line in text.split("\n")
                    if line.strip() and (line.strip().isupper() or line.strip().endswith(":")) and len(line.strip()) < 80
                ]
                pages.append(ParsedPage(page_number=i + 1, text=text, headings=headings))
            
            # Check if text was successfully extracted
            if any(p.text.strip() for p in pages):
                return pages
        except Exception as e:
            errors.append(f"pypdf error: {e}")

        # Strategy 2: pymupdf (fitz)
        try:
            import pymupdf
            doc = pymupdf.open(stream=content_bytes, filetype="pdf")
            pages = []
            for i, page in enumerate(doc):
                text = page.get_text() or ""
                headings = [
                    line.strip()
                    for line in text.split("\n")
                    if line.strip() and (line.strip().isupper() or line.strip().endswith(":")) and len(line.strip()) < 80
                ]
                pages.append(ParsedPage(page_number=i + 1, text=text, headings=headings))
            if any(p.text.strip() for p in pages):
                return pages
        except Exception as e:
            errors.append(f"pymupdf error: {e}")

        # Strategy 3: pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                pages = []
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    tables = []
                    try:
                        extracted_tables = page.extract_tables()
                        for tbl in extracted_tables:
                            rows = [" | ".join(str(cell or "").strip() for cell in r) for r in tbl if r]
                            if rows:
                                tables.append("\n".join(rows))
                    except Exception:
                        pass
                    headings = [
                        line.strip()
                        for line in text.split("\n")
                        if line.strip() and (line.strip().isupper() or line.strip().endswith(":")) and len(line.strip()) < 80
                    ]
                    pages.append(ParsedPage(page_number=i + 1, text=text, tables=tables, headings=headings))
            if any(p.text.strip() for p in pages):
                return pages
        except Exception as e:
            errors.append(f"pdfplumber error: {e}")

        # Strategy 4: Fallback raw stream text extraction
        try:
            raw_text = content_bytes.decode("utf-8", errors="ignore")
            # Filter printable strings of decent length
            printable = re.findall(r'[A-Za-z0-9\s.,!?:;\-–—\(\)\[\]/@#&%]{4,}', raw_text)
            extracted = "\n".join(printable)
            if extracted.strip():
                return [ParsedPage(page_number=1, text=extracted, headings=["Recovered PDF Content"])]
        except Exception:
            pass

        # If pages were created but are empty (e.g. scanned image-only PDF)
        if pages:
            return pages

        raise RuntimeError(f"Failed to parse PDF document ({filename}): " + "; ".join(errors))


class DocxParser(BaseDocumentParser):
    def parse(self, content_bytes: bytes, filename: str) -> List[ParsedPage]:
        import docx
        doc = docx.Document(io.BytesIO(content_bytes))
        full_text = []
        headings = []
        tables = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if p.style and "Heading" in p.style.name:
                headings.append(text)
            full_text.append(text)

        for table in doc.tables:
            rows = []
            for row in table.rows:
                row_text = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                rows.append("| " + " | ".join(row_text) + " |")
            if rows:
                tables.append("\n".join(rows))

        combined = "\n\n".join(full_text)
        if tables:
            combined += "\n\n### Extracted Tables:\n" + "\n\n".join(tables)

        return [ParsedPage(page_number=1, text=combined, tables=tables, headings=headings)]


class PPTXParser(BaseDocumentParser):
    def parse(self, content_bytes: bytes, filename: str) -> List[ParsedPage]:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(content_bytes))
        pages = []
        for i, slide in enumerate(prs.slides):
            slide_texts = []
            slide_headings = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text = paragraph.text.strip()
                        if text:
                            slide_texts.append(text)
                            if shape == slide.shapes[0]:  # Title shape usually
                                slide_headings.append(text)
            pages.append(ParsedPage(page_number=i + 1, text="\n".join(slide_texts), headings=slide_headings))
        return pages


class SpreadsheetParser(BaseDocumentParser):
    def parse(self, content_bytes: bytes, filename: str) -> List[ParsedPage]:
        pages = []
        if filename.endswith(".csv"):
            import csv
            text_data = content_bytes.decode("utf-8", errors="replace")
            reader = csv.reader(io.StringIO(text_data))
            rows = []
            for row in reader:
                rows.append("| " + " | ".join(row) + " |")
            table_md = "\n".join(rows[:500])  # limit rows for safety
            pages.append(ParsedPage(page_number=1, text=f"### CSV Data:\n{table_md}", tables=[table_md]))
        else:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True)
            for idx, sheet_name in enumerate(wb.sheetnames):
                sheet = wb[sheet_name]
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    if any(cell is not None for cell in row):
                        cleaned = [str(c).replace("\n", " ") if c is not None else "" for c in row]
                        rows.append("| " + " | ".join(cleaned) + " |")
                sheet_md = f"### Sheet: {sheet_name}\n" + "\n".join(rows[:300])
                pages.append(ParsedPage(page_number=idx + 1, text=sheet_md, tables=[sheet_md], headings=[sheet_name]))
        return pages


class HTMLParser(BaseDocumentParser):
    def parse(self, content_bytes: bytes, filename: str) -> List[ParsedPage]:
        html_str = content_bytes.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html_str, "html.parser")
        
        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Remove irrelevant noise
        for tag in soup(["script", "style", "noscript", "svg", "form", "iframe"]):
            tag.decompose()

        headings = []
        if title:
            headings.append(title)
            
        for h in soup.find_all(["h1", "h2", "h3"]):
            htxt = h.get_text().strip()
            if htxt and htxt not in headings:
                headings.append(htxt)

        tables = []
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text().strip().replace("\n", " ") for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append("| " + " | ".join(cells) + " |")
            if rows:
                tables.append("\n".join(rows))

        text = soup.get_text(separator="\n\n", strip=True)
        if title and not text.startswith(title):
            text = f"# {title}\n\n{text}"

        return [ParsedPage(page_number=1, text=text, tables=tables, headings=headings)]


class TextParser(BaseDocumentParser):
    def parse(self, content_bytes: bytes, filename: str) -> List[ParsedPage]:
        text = content_bytes.decode("utf-8", errors="replace")
        headings = [line.strip("# ").strip() for line in text.split("\n") if line.startswith("#")]
        return [ParsedPage(page_number=1, text=text, headings=headings)]


def get_parser(filename: str, mime_type: str = "") -> BaseDocumentParser:
    fn = (filename or "").lower()
    mt = (mime_type or "").lower()
    if fn.endswith(".pdf") or "pdf" in mt:
        return PDFParser()
    elif fn.endswith(".docx") or "wordprocessingml" in mt:
        return DocxParser()
    elif fn.endswith((".pptx", ".ppt")) or "presentationml" in mt:
        return PPTXParser()
    elif fn.endswith((".xlsx", ".xls", ".csv")) or "spreadsheet" in mt or "csv" in mt:
        return SpreadsheetParser()
    elif fn.endswith((".html", ".htm")) or "html" in mt:
        return HTMLParser()
    else:
        return TextParser()
