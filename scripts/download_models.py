"""Download the embedding and reranker models once, so later runs work offline.
The LLM (GGUF file) is downloaded separately; see PROJECT DOCUMENT, section Setup."""
from sentence_transformers import CrossEncoder, SentenceTransformer

from common import config

for name in [config.EMBED_MODEL, config.EMBED_MODEL_B]:
    m = SentenceTransformer(name, device="cpu")
    print(name, "dims", m.get_sentence_embedding_dimension())
r = CrossEncoder(config.RERANK_MODEL, device="cpu")
print(config.RERANK_MODEL, "ok")
