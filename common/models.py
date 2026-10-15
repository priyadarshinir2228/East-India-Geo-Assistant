"""Local embedding and reranker models.

Real models run through sentence-transformers. MODEL_BACKEND=stub swaps in tiny deterministic
stand-ins so the plumbing can be smoke-tested on a machine without the model weights.
Numbers produced with the stub are NOT reported anywhere.
"""
import hashlib
import math
import os
import re
import time

import numpy as np

from common import config

BACKEND = os.getenv("MODEL_BACKEND", "real")

# Query/passage prefixes each model was trained with.
PREFIXES = {
    "BAAI/bge-small-en-v1.5": ("Represent this sentence for searching relevant passages: ", ""),
    "intfloat/e5-base-v2": ("query: ", "passage: "),
}

_cache = {}


class Embedder:
    def __init__(self, name=None):
        self.name = name or config.EMBED_MODEL
        self.q_prefix, self.p_prefix = PREFIXES.get(self.name, ("", ""))
        if BACKEND == "stub":
            self.dims, self.model = 384, None
        else:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.name, device="cpu")
            self.dims = self.model.get_sentence_embedding_dimension()

    def _encode(self, texts, batch_size=32):
        if self.model is None:
            return np.vstack([_stub_vec(t, self.dims) for t in texts])
        # normalize_embeddings=True -> unit vectors, so cosine = dot product
        return self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True, convert_to_numpy=True)

    def passages(self, texts, batch_size=32):
        return self._encode([self.p_prefix + t for t in texts], batch_size)

    def query(self, text):
        return self._encode([self.q_prefix + text])[0]


class Reranker:
    """Cross-encoder: scores (query, passage) pairs jointly. Returns raw logits."""

    def __init__(self, name=None, max_length=512):
        self.name = name or config.RERANK_MODEL
        self.max_length = max_length  # longer passages are truncated by the tokenizer
        if BACKEND == "stub":
            self.model = None
        else:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.name, max_length=max_length, device="cpu")

    def score(self, query, passages, batch_size=16):
        if self.model is None:
            return np.array([_stub_overlap(query, p) for p in passages])
        # activation_fn=Identity keeps raw logits so we can apply our own sigmoid / temperature
        import torch
        return np.asarray(self.model.predict([(query, p) for p in passages], batch_size=batch_size,
                                             activation_fn=torch.nn.Identity(), show_progress_bar=False))


def get_embedder(name=None):
    key = ("emb", name or config.EMBED_MODEL)
    if key not in _cache:
        _cache[key] = Embedder(name)
    return _cache[key]


def get_reranker():
    if "rr" not in _cache:
        _cache["rr"] = Reranker()
    return _cache["rr"]


# ---- stub models (smoke tests only) ----
_TOK = re.compile(r"[a-z0-9]+")


def _stub_vec(text, dims):
    v = np.zeros(dims, dtype=np.float32)
    toks = _TOK.findall(text.lower())
    for t in toks + [a + "_" + b for a, b in zip(toks, toks[1:])]:
        h = int(hashlib.md5(t.encode()).hexdigest(), 16)
        v[h % dims] += 1 if (h >> 8) % 2 else -1
    n = np.linalg.norm(v)
    return v / n if n else v


def _stub_overlap(q, p):
    qs, ps = set(_TOK.findall(q.lower())), set(_TOK.findall(p.lower()))
    return 6 * len(qs & ps) / (math.sqrt(len(qs) + 1) * math.sqrt(len(ps) + 1)) - 2


def timed(fn, *a, **k):
    t = time.perf_counter()
    out = fn(*a, **k)
    return out, time.perf_counter() - t
