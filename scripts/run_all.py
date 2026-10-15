"""Run the whole PoC in order on the laptop (cross-platform). Each step is a plain module you can
also run on its own. Usage:
  python -m scripts.run_all setup     # GeoServer + Elasticsearch security and indices
  python -m scripts.run_all ingest    # ingest twice and show equal counts
  python -m scripts.run_all eval      # every results table into evalsuite/results/
  python -m scripts.run_all all
"""
import subprocess
import sys
import time

PY = sys.executable
STEPS = {
    "setup": [["geoserver.setup_geoserver"], ["geoserver.check_access"], ["es.setup_security"],
              ["es.setup_indices", "--dims", "384"], ["es.cluster_health"]],
    "ingest": [["ingest.run_ingest"], ["ingest.run_ingest"]],
    "eval": [["evalsuite.model_info"], ["evalsuite.eval_extraction"], ["evalsuite.eval_resolution"],
             ["evalsuite.eval_embeddings"], ["evalsuite.eval_ann"], ["evalsuite.paging_demo"], ["evalsuite.eval_graph"],
             ["evalsuite.eval_retrieval"], ["evalsuite.eval_rerank", "--llm-scorer"], ["evalsuite.eval_confidence"],
             ["evalsuite.eval_sampling"], ["evalsuite.eval_dev"]],
}


def run(group):
    for step in STEPS[group]:
        t = time.perf_counter()
        print(f"\n=== python -m {' '.join(step)}", flush=True)
        r = subprocess.run([PY, "-m", *step])
        print(f"=== {'ok' if r.returncode == 0 else 'FAILED'} in {time.perf_counter() - t:.0f}s", flush=True)
        if r.returncode:
            sys.exit(r.returncode)


if __name__ == "__main__":
    groups = sys.argv[1:] or ["all"]
    for g in (["setup", "ingest", "eval"] if groups == ["all"] else groups):
        run(g)
