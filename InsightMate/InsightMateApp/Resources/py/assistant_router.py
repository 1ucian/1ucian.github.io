import re
from typing import Optional

from onedrive_reader import search, list_word_docs

ONEDRIVE_KEYWORDS = {'onedrive', 'search', 'summarize', 'find', 'list'}


def route_query(query: str) -> Optional[str]:
    q = query.lower()
    if any(k in q for k in ONEDRIVE_KEYWORDS):
        if 'list' in q and 'word' in q:
            docs = list_word_docs()
            return 'Word docs:\n' + '\n'.join(docs)
        results = search(query)
        if not results:
            return 'No matching documents found.'
        lines = []
        for r in results:
            snippet = f" - {r['snippet']}" if r.get('snippet') else ''
            lines.append(f"{r['name']}{snippet}")
        return '\n'.join(lines)
    return None
