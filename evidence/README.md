# Evidence

Screenshots and logs captured on the laptop for the demo:

- `docker compose ps` with all services up
- `python -m es.cluster_health` (green) and `python -m geoserver.check_access` (401 / 200 / 403)
- the two ingest runs with equal counts (`python -m scripts.run_all ingest`)
- the Streamlit UI answering, abstaining and refusing
- `requests.jsonl`: one line per question asked (written by the app, not committed)
