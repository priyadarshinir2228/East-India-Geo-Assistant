"""Draw diagram/architecture.png (matplotlib only). Run: python diagram/make_diagram.py"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 160)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, title, lines=(), color="#e8eef7", edge="#3a5a8c"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=color, ec=edge, lw=1.3))
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="top", fontsize=10.5, fontweight="bold")
    for i, l in enumerate(lines):
        ax.text(x + w / 2, y + h - 6.3 - 3.1 * i, l, ha="center", va="top", fontsize=8.6, color="#222")


def arrow(x1, y1, x2, y2, label=None):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, lw=1.2, color="#555"))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.2, label, ha="center", fontsize=8, color="#555")


ax.text(2, 97, "East India Geo-Assistant: architecture (all on localhost)", fontsize=15, fontweight="bold")
ax.text(2, 93.5, "INGESTION", fontsize=11, fontweight="bold", color="#3a5a8c")
ax.text(2, 47, "RETRIEVAL", fontsize=11, fontweight="bold", color="#8c3a3a")

# ingestion lane
box(2, 72, 24, 18, "Documents", ["data/corpus: MD, TXT, PDF", "circulars, guidelines,", "school + town notes"])
box(2, 50, 24, 18, "GeoServer :8080", ["workspace east_india", "schools, roads, landuse", "WFS GeoJSON as rag_geo", "(read-only, anon = 401)"], "#eef7e8", "#4a7a3a")
box(34, 76, 26, 14, "Load + chunk", ["700 chars, 120 overlap", "page + char spans kept"])
box(34, 56, 26, 16, "Extract entities", ["rules + gazetteer (default)", "LLM JSON (schema-validated)", "8 types"])
box(66, 56, 26, 16, "Resolve + link", ["string similarity >= 88", "acronym + initials rules", "school -> osm_id"])
box(66, 76, 26, 14, "Embed", ["bge-small-en-v1.5 (384-d)", "e5-base-v2 compared"])
box(98, 56, 26, 16, "Build relations", ["6 types + noisy-OR weights", "near: <=300 m in EPSG:32646", "evidence: chunk or geoserver"])
box(130, 46, 28, 46, "Elasticsearch :9200", ["single node, heap 2 GB", "auth on; app uses role rag_app", "(API key, 3 indices only)", "",
                                             "east_india_chunks", "BM25 text + dense_vector", "int8_hnsw m=16 efc=100", "",
                                             "east_india_entities", "nested mentions, geo_point", "", "east_india_relations"], "#f7f1e8", "#8c6a3a")
arrow(26, 81, 34, 83)
arrow(47, 76, 47, 72)
arrow(26, 59, 34, 62, "gazetteer")
arrow(60, 64, 66, 64)
arrow(60, 83, 66, 83)
arrow(92, 64, 98, 64)
arrow(26, 52.5, 98, 57.5)
ax.text(62, 52.3, "geometries (WFS)", fontsize=8, color="#555")
arrow(92, 83, 130, 83, "bulk index, deterministic IDs")
arrow(124, 64, 130, 64)

# retrieval lane
box(2, 26, 22, 16, "Question", ["Streamlit :8501 / CLI", "safety screen: refuse", "write, secret, off-topic"], "#f7e8e8", "#8c3a3a")
box(30, 26, 22, 16, "Detect entities", ["rules + corpus aliases", "-> entity IDs"])
box(58, 26, 26, 16, "Graph-hybrid search", ["BM25 + kNN (RRF k=60)", "+ graph expand (2 hops)", "metadata / geo_distance filters"])
box(90, 26, 22, 16, "Rerank", ["bge-reranker-base", "cross-encoder, top 20", "ties by chunk_id"])
box(118, 24, 40, 18, "LLM  llama-server :8081", ["Qwen2.5 Instruct GGUF (Q4_K_M), greedy", "top 5 passages + graph/GeoServer facts", "JSON: answer, citations, confidence,", "entities_used; citations checked"], "#efe8f7", "#5a3a8c")
box(118, 3, 40, 17, "Confidence", ["sigmoid(s/T), margin, agreement,", "answer token log-probabilities", "-> logistic regression -> threshold"])
box(58, 3, 50, 18, "Answer or abstain", ["confidence < threshold or no evidence ->", "\"I cannot answer this from the available sources\"",
                                           "UI shows answer, citations, confidence,", "entities, graph path, settings"], "#f7e8e8", "#8c3a3a")
box(2, 3, 50, 18, "Untrusted data stays data", ["passages + facts wrapped in <passage>/<fact>,", "escaped, flagged if instruction-like;",
                                                  "system prompt: never follow text inside them"], "#f2f2f2", "#666")
arrow(24, 34, 30, 34)
arrow(52, 34, 58, 34)
arrow(84, 34, 90, 34)
arrow(112, 34, 118, 34)
arrow(138, 24, 138, 20)
arrow(118, 12, 108, 12)
arrow(140, 46, 76, 42, "rag_app reads")
Path(__file__).with_name("architecture.png").parent.mkdir(exist_ok=True)
plt.savefig(Path(__file__).with_name("architecture.png"), dpi=130, bbox_inches="tight")
print("wrote diagram/architecture.png")
