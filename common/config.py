"""Settings read from environment variables (.env). No secrets live in code."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_API_KEY = os.getenv("ES_API_KEY", "")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "")

GEOSERVER_URL = os.getenv("GEOSERVER_URL", "http://localhost:8080/geoserver")
GEOSERVER_ADMIN_PASSWORD = os.getenv("GEOSERVER_ADMIN_PASSWORD", "")
RAG_GEO_USER = os.getenv("RAG_GEO_USER", "rag_geo")
RAG_GEO_PASSWORD = os.getenv("RAG_GEO_PASSWORD", "")
GS_WORKSPACE = "east_india"

LLM_URL = os.getenv("LLM_URL", "http://localhost:8081")
LLM_MODEL = os.getenv("LLM_MODEL", "local")

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
EMBED_MODEL_B = os.getenv("EMBED_MODEL_B", "intfloat/e5-base-v2")
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-base")

# Elasticsearch index names must be lowercase with no spaces, so
# "East India_chunks" becomes "east_india_chunks" (see PROJECT DOCUMENT).
CHUNKS_INDEX = "east_india_chunks"
ENTITIES_INDEX = "east_india_entities"
RELATIONS_INDEX = "east_india_relations"

DATA = ROOT / "data"
CORPUS_DIR = DATA / "corpus"
EVAL_DIR = DATA / "eval"
LAYERS_GPKG = DATA / "geoserver" / "east_india.gpkg"
RESULTS = ROOT / "evalsuite" / "results"
WORK = DATA / "work"          # intermediate JSONL (chunks, entities, relations)
