"""Split documents into overlapping chunks that keep page numbers and character spans.

Strategy: pack whole sentences (split on . ! ? or line breaks) until the chunk would pass
CHUNK_CHARS, then start the next chunk OVERLAP_CHARS back so a fact on the boundary
appears whole in at least one chunk. ~700 characters is about 150 tokens: one or two
paragraphs, well under the 512-token limit of the embedder and reranker.
"""
import re

CHUNK_CHARS = 700
OVERLAP_CHARS = 120
SENT = re.compile(r"[^.!?\n]+(?:[.!?]+|\n+|$)")


def _sentences(text):
    return [(m.start(), m.end()) for m in SENT.finditer(text) if m.group().strip()]


def chunk_document(doc, size=CHUNK_CHARS, overlap=OVERLAP_CHARS):
    """Chunk page by page, so no chunk crosses a PDF page boundary."""
    chunks = []
    for page_no, p_start, p_end in doc["pages"]:
        sents = [(p_start + s, p_start + e) for s, e in _sentences(doc["text"][p_start:p_end])]
        i = 0
        while i < len(sents):
            start, end, j = sents[i][0], sents[i][1], i + 1
            while j < len(sents) and sents[j][1] - start <= size:
                end, j = sents[j][1], j + 1
            raw = doc["text"][start:end]
            s0 = start + len(raw) - len(raw.lstrip())  # trim whitespace but keep offsets exact
            e0 = end - (len(raw) - len(raw.rstrip()))
            chunks.append({
                "chunk_id": f"{doc['doc_id']}:{s0}-{e0}",  # deterministic: same input -> same id
                "doc_id": doc["doc_id"], "file": doc["file"], "doc_kind": doc["kind"], "title": doc["title"],
                "text": doc["text"][s0:e0], "start": s0, "end": e0, "page": page_no, "n_chars": e0 - s0,
            })
            if j >= len(sents):
                break
            # next chunk starts at the earliest sentence that begins after (end - overlap)
            k = j
            while k > i + 1 and sents[k - 1][0] >= end - overlap:
                k -= 1
            i = k
    return chunks
