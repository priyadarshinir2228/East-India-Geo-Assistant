# East India Geo Assistant

Local RAG proof of concept: admission circulars in Elasticsearch, school, road and locality layers in GeoServer, a local LLM through llama.cpp, and answers with citations, calibrated confidence and abstention.

Quick start (details, versions and design notes in [PROJECT DOCUMENT.md](PROJECT%20DOCUMENT.md)):

```bash
pip install -r requirements.txt
cp .env.example .env          # set your own passwords
docker compose up -d
python -m scripts.download_models
llama-server -m models/Qwen2.5-3B-Instruct-Q4_K_M.gguf --port 8081 -c 8192 --jinja   # separate terminal
python -m scripts.run_all     # setup, ingest twice, all evaluations
streamlit run app/streamlit_app.py
```

| Folder | Contents |
|---|---|
| `es/`, `geoserver/` | security and index / layer setup |
| `ingest/` | loading, chunking, extraction, resolution, relations, indexing |
| `retrieve/` | search modes, graph expansion, reranking, confidence |
| `app/` | assistant pipeline, CLI, Streamlit UI, safety |
| `evalsuite/` | metrics (own code) and Task 1–8 evaluations |
| `data/` | corpus, evaluation sets, GeoServer layers |
| `diagram/` | architecture diagram |
| `evidence/` | screenshots and logs for the demo |
