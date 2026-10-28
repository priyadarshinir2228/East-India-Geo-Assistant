# East India Geo Assistant: Project Document

A local retrieval-augmented assistant that answers questions about school admissions in East India. It combines admission circulars and school notes (in Elasticsearch) with school, road and locality layers (served by GeoServer), and answers with citations, a calibrated confidence, and abstention when the sources do not support an answer.

Everything runs on one laptop (16 GB RAM) on localhost, with free software only.

## 1. Setup

### Versions

| Component | Version | Port (localhost only) |
|---|---|---|
| Docker | 29.5.3 | |
| Elasticsearch | 8.17.4 (single node, 2 GB fixed heap) | 9200 |
| Kibana | 8.17.4 | 5601 |
| GeoServer | 2.26.1 (kartoza/geoserver image) | 8080 |
| llama.cpp `llama-server` | any recent release | 8081 |
| Python | 3.10 or newer | |
| Streamlit UI | 1.45.1 | 8501 |

All container ports are bound to `127.0.0.1`, so nothing is reachable from the network.

### Models (all local)

| Role | Model | Notes |
|---|---|---|
| Embedding A (default) | BAAI/bge-small-en-v1.5 | 384 dims; query prefix "Represent this sentence for searching relevant passages: " |
| Embedding B (compared) | intfloat/e5-base-v2 | 768 dims; "query: " and "passage: " prefixes |
| Reranker | BAAI/bge-reranker-base | cross-encoder, raw logits |
| LLM | Qwen2.5-3B-Instruct, GGUF Q4_K_M | served by llama-server; the 7B Q4_K_M also fits in 16 GB but is slower |

### Steps

```bash
# 1. Python environment
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # CPU torch is enough

# 2. Secrets: copy the template and choose your own passwords
cp .env.example .env                 # edit ELASTIC_PASSWORD, KIBANA_PASSWORD, GEOSERVER_ADMIN_PASSWORD, RAG_GEO_PASSWORD

# 3. Services
docker compose up -d
docker compose ps                    # wait until elasticsearch and geoserver are up

# 4. Local models (one-off download, then everything works offline)
python -m scripts.download_models
#    LLM: download Qwen2.5-3B-Instruct-Q4_K_M.gguf (bartowski/Qwen2.5-3B-Instruct-GGUF on Hugging Face)
#    into models/, then in a separate terminal:
llama-server -m models/Qwen2.5-3B-Instruct-Q4_K_M.gguf --port 8081 -c 8192 --jinja

# 5. Setup, ingestion and every evaluation table
python -m scripts.run_all setup      # GeoServer workspace, layers, users, ACLs; ES role, API key, indices
python -m scripts.run_all ingest     # runs ingestion twice to show it is idempotent
python -m scripts.run_all eval       # writes evalsuite/results/*.md

# 6. Use the assistant
python -m app.cli "Which board is Hare School affiliated with?"
streamlit run app/streamlit_app.py
```

The data the services need is already in the repository: the corpus in `data/corpus/`, the evaluation files in `data/eval/`, and the GeoServer layers in `data/geoserver/east_india.gpkg`. The scripts in `scripts/` (`world.py`, `make_layers.py`, `make_corpus.py`, `make_questions.py`) rebuild them from `data/raw/schools.gpkg` and are deterministic.

### Windows notes (the laptop used for the demo)

- **Python.** `.venv` is created from the system Python 3.12.10 (`C:\Users\ASUS\AppData\Local\Programs\Python\Python312`). `python -m scripts.check_env` checks every pinned package, the tools, the ports and the services in one go.
- **huggingface-hub.** transformers 4.52.4 refuses huggingface-hub 1.x or later, so `requirements.txt` pins `huggingface-hub==0.36.2`.
- **llama-server.** CMake 4.4 is installed, but building llama.cpp from source also needs the Visual Studio C++ Build Tools. The demo uses the official prebuilt CPU release instead (`llama-b11622-bin-win-cpu-x64.zip` from github.com/ggml-org/llama.cpp), unpacked to `D:\llama-bin`:
  `D:\llama-bin\llama-server.exe -m models\Qwen2.5-3B-Instruct-Q4_K_M.gguf --host 127.0.0.1 --port 8081 -c 8192 --jinja`
- **VS Code.** `.vscode/tasks.json` has one task per step (services, llama-server, status, setup, ingest, eval, CLI, Streamlit, tests). Each runs in its own terminal: Ctrl+Shift+P, then "Tasks: Run Task".
- **Run only one llama-server.** A second one on the same port breaks the requests that are in flight.
- **pytest** only collects `tests/` (`pytest.ini`), so the bundled llama.cpp tests are skipped.

### Notes

- **Index names.** The brief names the indices "East India_chunks", "East India_entities" and "East India_relations". Elasticsearch rejects upper-case letters and spaces in index names, so they are `east_india_chunks`, `east_india_entities` and `east_india_relations`.
- **Disk watermark.** Elasticsearch stops allocating shards when the disk is more than 85–90% full and the cluster turns yellow or red. If `python -m es.cluster_health` shows that, free disk space. Do not turn the watermark off in a real deployment.
- **Replicas** are 0 on every index, so the single node reports green.
- **Memory budget** (about 9 GB): Elasticsearch 3 GB, GeoServer 1.5 GB, Kibana 1 GB, llama-server with the 3B model about 3 GB, Python models about 1 GB.

## 2. Data

| Item | Source | Size |
|---|---|---|
| School buildings | OpenStreetMap via the supplied `schools.gpkg` (layer `gis_osm_buildings_a_free_1`) | 1,062 features |
| Board, seats, cut-off marks per school | **synthetic**, generated by `scripts/world.py` | |
| Roads and localities | **synthetic** schematic lines and locality discs placed around real schools | |
| Corpus | 68 documents: 9 circulars (one PDF), 3 guidelines, 18 school notes, 3 town notes, 34 per-town school directories built from real OSM names, 1 community board post | 162 chunks |
| Gold entities | 10 documents, 94 mentions with exact character spans | |
| Retrieval questions | 30 (split tune / holdout), graded 0/1/2 by evidence substrings | |
| Calibration questions | 40 (split fit / test) | |
| Dev questions | 10, including unanswerable, write-intent and injection cases | |

The circulars, rules and school attributes are invented so that every answer can be checked. School names and locations are real OSM data. `community_board_post.txt` contains a prompt-injection attempt on purpose.

## 3. Security

### Elasticsearch

- Security is on. The `elastic` superuser is used only by `es/setup_security.py` and `es/setup_indices.py`.
- Role `rag_app` has cluster `monitor` and `read`, `write`, `view_index_metadata` on the three indices only. It cannot create or delete indices, change mappings, or manage users.
- The application authenticates with an API key bound to that role. The key is written to `.env` and never printed.
- HTTP TLS is off because the port is bound to 127.0.0.1. Any deployment beyond one laptop must turn it on.

### GeoServer

- Workspace `east_india` with a GeoPackage store and layers `schools`, `roads`, `landuse`.
- User `rag_geo` with role `ROLE_RAG_GEO`. Layer rules: `east_india.*.r = ROLE_RAG_GEO,ADMIN`, `east_india.*.w = ADMIN`. Catalogue mode CHALLENGE.
- `python -m geoserver.check_access` shows: anonymous WFS gets 401, `rag_geo` reads GeoJSON, and a WFS-T insert by `rag_geo` gets 403.

### Secrets

No password, key or token is in any committed file. `.env` is in `.gitignore`; `.env.example` holds placeholders.

### Untrusted text

- Requests are screened before retrieval: write intent, requests for secrets or prompts, and off-topic questions are refused (`app/safety.py`).
- Retrieved passages and GeoServer facts reach the model only inside escaped `<passage>` and `<fact>` tags. The system prompt says text inside them is data and must never be followed.
- Passages that look like injections are flagged in the log.
- The model's output must match a JSON schema; citations not in the retrieved set are reported as invalid.

## 4. Ingestion (Tasks 1–2)

`python -m ingest.run_ingest [--extractor rules|llm|hybrid]` runs: load, chunk, extract, resolve, relations, embed, index.

- **Loading.** Markdown, text and PDF (page by page, so page numbers survive).
- **Chunking.** 700 characters with 120 overlap, cut at paragraph or sentence ends where possible, never across pages. Chunk IDs are `doc_id:start-end`, so they do not change between runs.
- **Extraction.** Entity types: School, Board, Road, Locality, Circular, Date, Quantity, Rule.
  - The rule extractor uses regular expressions plus a gazetteer built from the GeoServer layers.
  - The LLM extractor asks llama-server for JSON that must match a schema and checks every span against the text.
  - Both are scored against the gold spans (exact and overlap F1).
- **Resolution.** Schools are linked to GeoServer features by fuzzy name similarity (rapidfuzz), an acronym rule (SXCS, DPS), an initials rule ("K.K." to "Krishna Kumar"), and a location tie-break. Same-name buildings within 1 km are one school. The link threshold (88) is chosen on a sweep in `task2_resolution.md`.
- **Relations.** `affiliated_with`, `applies_to`, `mentions`, `located_in`, `near` (300 m, measured in EPSG:32646), `supersedes`, `states`. Each has a weight and evidence (a chunk ID or "geoserver"). Independent evidence is combined with noisy-OR.
- **Idempotency.** Every document has a deterministic ID; bulk writes overwrite, and documents from an earlier run that no longer exist are deleted. Two runs give identical counts (`task2_determinism.md`).

## 5. Retrieval (Tasks 3–6)

- **Mappings.** `embedding` is an int8-quantised HNSW `dense_vector` (m 16, ef_construction 100); `embedding_f32` is a float HNSW copy for the ANN comparison. Metadata fields hold board, school IDs, issue date and school locations (`geo_point`).
- **Modes** (`retrieve/search.py`):
  - `keyword` (BM25)
  - `vector` (kNN, num_candidates 100)
  - `hybrid` (our own RRF, k 60, or a weighted sum)
  - `graph_hybrid` (RRF with a third list from graph expansion, weight 0.5)
  - All modes accept metadata filters and a `geo_distance` filter.
- **Graph** (`retrieve/graph.py`). The relations index is loaded into NetworkX. Breadth-first expansion up to 2 hops, a visited set against cycles, `max_expand` against fan-out, a penalty for passing through hub nodes, and `min_weight` 0.3.
- **Reranking.** The cross-encoder rescores the top 20; long passages are scored in windows. An optional LLM yes/no scorer is compared in `task6_rerank.md`.

## 6. Answering and confidence (Tasks 7–8)

- **Pipeline** (`app/pipeline.py`):
  1. Screen the request.
  2. Detect entities.
  3. Run graph-hybrid search.
  4. Rerank the results.
  5. Add graph and GeoServer facts.
  6. Generate a grounded JSON answer (temperature 0, seed 42).
  7. Compute confidence.
  8. Answer or abstain.
  - Every request is logged to `evidence/requests.jsonl`.
- **Confidence signals:**
  - Reranker probability of the top passage, `sigmoid(score / T)`.
  - Margin between the first and second passages.
  - Whether keyword and vector search agree on the top passage.
  - Answer probability `exp(mean token log-prob)`. When the server returns no log-probs, the agreement of 5 sampled answers is used instead.
- **Calibration.**
  - The signals are combined by logistic regression fitted on the 25 "fit" questions only. T is chosen by log loss on the same split.
  - The reliability table, ECE and Brier score are reported on the 15 "test" questions.
- **Abstention.** The threshold is the lowest value that gives at least 90% accuracy on the fit split. It is saved in `evalsuite/results/confidence_model.json` and used by the app.

## 7. Evaluation

All metric functions are our own (`evalsuite/metrics.py`, tested by `tests/test_metrics.py`): precision, recall, F1, P@k, Recall@k, MRR, nDCG, ECE, Brier and log loss.

| Task | Script | Output |
|---|---|---|
| 1 | `evalsuite.model_info`, `es.cluster_health`, `geoserver.check_access` | `task1_models.md` |
| 2 | `eval_extraction`, `eval_resolution`, ingest twice | `task2_*.md` |
| 3 | `eval_embeddings`, `eval_ann`, `paging_demo` | `task3_*.md` |
| 4 | `eval_graph` | `task4_graph.md` |
| 5 | `eval_retrieval` | `task5_*.md` |
| 6 | `eval_rerank --llm-scorer` | `task6_rerank.md` |
| 7 | `eval_confidence`, `eval_sampling` | `task7_*.md` |
| 8 | `eval_dev` | `task8_dev.md` |

Tuning uses only the "tune" and "fit" splits; the "holdout" and "test" splits are reported once.

### Failure analysis and the fix

Known failures in the pipeline:

1. "K.K. Hindu Academy" was not linked (score 66.7) because initials do not match full words. **Fixed** by the initials rule; it now links at 95. The before and after are in `task2_resolution.md`.
2. "C.R. Boys High School" stays unlinked (no feature scores above the threshold).
3. "Don Bosco Park Circus" is missed by the rule extractor.
4. "Kendriya Vidyalaya" is cut short from "Kendriya Vidyalaya Salt Lake" and links to a school in another town.
5. Graph noise: through a board hub, a cut-off question about Hare School reaches unrelated circulars. The hub penalty and `min_weight` reduce this but do not remove it.

## 8. Algorithm notes

- **BM25.** Scores a passage by how often query terms appear in it, weighted by how rare each term is in the corpus (IDF), with term frequency saturating (k1) and long passages penalised (b).
- **HNSW.** Approximate nearest-neighbour search on a layered graph of vectors: a greedy walk from the sparse top layer down to the dense bottom layer. `m` sets links per node, `ef_construction` sets build quality, and `num_candidates` sets search breadth. int8 quantisation stores each dimension in one byte, so recall can drop slightly; `task3_ann_vs_exact.md` measures it against exact search.
- **RRF.** Reciprocal rank fusion: each list contributes `w / (k + rank)` for each passage, and the sums are sorted. It needs only ranks, so BM25 and cosine scores do not have to be on the same scale.
- **Cross-encoder.** Reads the question and passage together and outputs one relevance logit. More accurate than comparing two separate embeddings, but it has to run once per pair, so it is used only on the top 20.
- **Softmax and temperature.** Softmax turns logits into probabilities. Dividing logits by T before softmax (or sigmoid) makes the probabilities softer (T > 1) or sharper (T < 1) without changing their order; that is temperature scaling.
- **Greedy decoding.** Temperature 0 picks the most likely token at every step, so the answer is repeatable. `task7_sampling.md` compares this with sampling (temperature, top-p and top-k).
- **Graph traversal.** Breadth-first search by hop count. The weight of a path is the product of its edge weights; it is halved when the path passes through a hub. A node is never visited twice.

## 9. Limitations

- The circulars, school attributes, roads and localities are synthetic. Results show that the method works, not how accurate it would be on real circulars.
- The evaluation sets are small (30, 40 and 10 questions), so differences of a few points are within noise.
- The rule extractor is tuned to this corpus's formats.
- One node, no TLS, and no backups: this is a proof of concept for one laptop.

## 10. Disclosures and credits

- **Data.** School buildings © OpenStreetMap contributors, licensed under ODbL 1.0. Everything else in `data/` is synthetic and generated by the scripts in `scripts/`.
- **Models.** BAAI bge-small-en-v1.5 and bge-reranker-base (MIT), intfloat e5-base-v2 (MIT), Qwen2.5-3B-Instruct (Qwen licence), via llama.cpp (MIT).
- **Software.** Elasticsearch and Kibana (Elastic License 2.0 / free tier), GeoServer (GPL 2.0), Python libraries listed in `requirements.txt`.
- **AI assistance.** The code, synthetic data and this document were written with the help of Claude (Anthropic), an AI assistant. All results in `evalsuite/results/` come from running the code locally.
