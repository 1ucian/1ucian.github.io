import os
from pathlib import Path
from typing import List, Dict, Optional

try:
    from docx import Document
except Exception:
    Document = None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    import textract
except Exception:
    textract = None

ONEDRIVE_DIR = os.path.join(os.path.expanduser('~'), 'OneDrive')
DOC_EXTS = {'.txt', '.md', '.docx', '.pdf'}


def _iter_files() -> List[Dict[str, str]]:
    files = []
    if not os.path.isdir(ONEDRIVE_DIR):
        return files
    for root, _dirs, filenames in os.walk(ONEDRIVE_DIR):
        for name in filenames:
            ext = Path(name).suffix.lower()
            if ext in DOC_EXTS:
                path = os.path.join(root, name)
                info = {
                    'name': name,
                    'path': path,
                    'modified': os.path.getmtime(path)
                }
                files.append(info)
    return files


_def_cache: Optional[List[Dict[str, str]]] = None


def index_files() -> List[Dict[str, str]]:
    """Return cached list of OneDrive documents with metadata."""
    global _def_cache
    if _def_cache is None:
        _def_cache = sorted(_iter_files(), key=lambda f: f['modified'], reverse=True)
    return _def_cache



def extract_text(path: str) -> str:
    """Best-effort plain text extraction."""
    ext = Path(path).suffix.lower()
    try:
        if ext in {'.txt', '.md'}:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        if ext == '.docx' and Document:
            doc = Document(path)
            return '\n'.join(p.text for p in doc.paragraphs)
        if ext == '.pdf' and PdfReader:
            reader = PdfReader(path)
            return '\n'.join(page.extract_text() or '' for page in reader.pages)
        if textract:
            return textract.process(path).decode('utf-8', errors='ignore')
    except Exception:
        pass
    return ''


def search(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """Search filenames and content for the query."""
    results = []
    q = query.lower()
    for info in index_files():
        if q in info['name'].lower():
            results.append({**info, 'snippet': ''})
        else:
            text = extract_text(info['path']).lower()
            if q in text:
                snippet_start = max(text.find(q) - 40, 0)
                snippet = text[snippet_start: snippet_start + 160]
                results.append({**info, 'snippet': snippet})
        if len(results) >= limit:
            break
    return results


def list_word_docs(limit: int = 20) -> List[str]:
    return [f['name'] for f in index_files() if f['name'].lower().endswith('.docx')][:limit]


if __name__ == '__main__':
    for item in search('test'):
        print(f"{item['name']} - {item['path']}")

