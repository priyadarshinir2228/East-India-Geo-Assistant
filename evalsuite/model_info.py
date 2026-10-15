"""Task 1.3 / 1.4: record the LLM, embedders and reranker (size, quantisation, context, speed, memory, outputs)."""
import json
import os
import time

import numpy as np

from common import config, llm
from common.io import write_md_table
from common.models import Embedder, Reranker


def rss_mb():
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 2 ** 20
    except ImportError:
        return float("nan")


def main():
    rows = []
    props = llm.server_props()
    gen = props.get("default_generation_settings", {})
    t = time.perf_counter()
    res = llm.chat([{"role": "user", "content": "In two sentences, what is a school admission circular?"}], max_tokens=128)
    rows.append(["LLM", props.get("model_path", config.LLM_MODEL), f"n_ctx={gen.get('n_ctx', props.get('n_ctx', '?'))}",
                 f"{res['tokens_per_second']:.1f} tok/s" if res["tokens_per_second"] else "?",
                 "see llama-server log / Task Manager", f"text + logprobs={bool(res['token_logprobs'])}"])
    for name in [config.EMBED_MODEL, config.EMBED_MODEL_B]:
        before = rss_mb()
        e = Embedder(name)
        v = e.passages(["Hare School is a WBBSE school in College Street."] * 64)
        t = time.perf_counter()
        e.passages(["Hare School is a WBBSE school in College Street."] * 64)
        rows.append(["embedder", name, f"dims={e.dims}", f"{64 / (time.perf_counter() - t):.0f} texts/s",
                     f"+{rss_mb() - before:.0f} MB", f"unit vector, norm={np.linalg.norm(v[0]):.2f}"])
    before = rss_mb()
    r = Reranker()
    s = r.score("minimum age for class I", ["The minimum age for Class I is 6 years.", "Jessore Road is closed."])
    rows.append(["reranker", r.name, f"max_length={r.max_length}", "-", f"+{rss_mb() - before:.0f} MB",
                 f"raw logit per pair, e.g. {s[0]:.2f} vs {s[1]:.2f}"])
    write_md_table(config.RESULTS / "task1_models.md", "Task 1: models",
                   ["Component", "Model", "Context / size", "Speed", "Memory", "Output"], rows,
                   notes="LLM parameter count and quantisation come from the GGUF file name and the llama-server start-up log.\n\n"
                         "```json\n" + json.dumps({k: props.get(k) for k in ("model_path", "total_slots", "build_info")}, indent=1) + "\n```")


if __name__ == "__main__":
    main()
