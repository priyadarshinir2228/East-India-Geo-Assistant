"""Load Markdown, text and PDF documents as plain text with page boundaries."""
import json
import re

from pypdf import PdfReader

from common import config

DATE_LINE = re.compile(r"^(?:Date|Issued|Issued on|Issued:)\s*:?\s*(.+)$", re.M)


def load_documents():
    """Yield dicts: doc_id, file, kind, text, pages=[(page_no, start, end)]."""
    manifest = json.loads((config.DATA / "corpus_manifest.json").read_text(encoding="utf-8"))
    for m in manifest:
        path = config.CORPUS_DIR / m["file"]
        if path.suffix == ".pdf":
            parts, pages, pos = [], [], 0
            for i, page in enumerate(PdfReader(str(path)).pages, start=1):
                t = (page.extract_text() or "").strip()
                parts.append(t)
                pages.append((i, pos, pos + len(t)))
                pos += len(t) + 2  # "\n\n" joiner
            text = "\n\n".join(parts)
        else:
            text = path.read_text(encoding="utf-8")
            pages = [(1, 0, len(text))]
        title = text.strip().splitlines()[0].lstrip("# ").strip()
        yield {**m, "text": text, "pages": pages, "title": title}
