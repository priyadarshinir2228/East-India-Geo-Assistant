"""Client for the local LLM server (llama.cpp `llama-server`, OpenAI-compatible API).

Every call returns the text, token log-probabilities (if the server sends them) and timing.
"""
import json
import os
import time

import requests

from common import config

BACKEND = os.getenv("LLM_BACKEND", "server")


def chat(messages, temperature=0.0, top_p=1.0, top_k=40, max_tokens=512, seed=42, json_schema=None, logprobs=True,
         top_logprobs=0):
    if BACKEND == "stub":
        from common.llm_stub import stub_chat
        return stub_chat(messages, json_schema)
    body = {"model": config.LLM_MODEL, "messages": messages, "temperature": temperature, "top_p": top_p,
            "top_k": top_k, "max_tokens": max_tokens, "seed": seed, "logprobs": logprobs, "stream": False}
    if top_logprobs:
        body["top_logprobs"] = top_logprobs
    if json_schema is not None:
        # llama-server turns the schema into a grammar, so output is always parseable JSON
        body["response_format"] = {"type": "json_object", "schema": json_schema}
    t = time.perf_counter()
    r = requests.post(config.LLM_URL + "/v1/chat/completions", json=body, timeout=300)
    r.raise_for_status()
    dt = time.perf_counter() - t
    out = r.json()
    choice = out["choices"][0]
    lp = choice.get("logprobs") or {}
    content = lp.get("content") or []
    token_logprobs = [c["logprob"] for c in content if "logprob" in c]
    top = [{t["token"]: t["logprob"] for t in c.get("top_logprobs", [])} for c in content]
    usage = out.get("usage", {})
    n_out = usage.get("completion_tokens") or len(token_logprobs)
    return {"text": choice["message"]["content"], "token_logprobs": token_logprobs, "top_logprobs": top, "seconds": dt,
            "completion_tokens": n_out, "prompt_tokens": usage.get("prompt_tokens"),
            "tokens_per_second": (n_out / dt) if dt else None}


def chat_json(messages, schema, **kw):
    """Chat and parse JSON. Returns (obj or None, raw response)."""
    res = chat(messages, json_schema=schema, **kw)
    try:
        return json.loads(res["text"]), res
    except json.JSONDecodeError:
        return None, res


def server_props():
    """Model metadata reported by llama-server (/props) for the PROJECT DOCUMENT."""
    try:
        return requests.get(config.LLM_URL + "/props", timeout=10).json()
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
