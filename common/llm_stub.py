"""Deterministic stand-in for the LLM, used only for smoke tests without model weights."""
import json
import re


def stub_chat(messages, schema):
    user = messages[-1]["content"]
    if schema and "answer" in json.dumps(schema):
        ids = re.findall(r'<passage id="([^"]+)"', user)
        body = user.split(">", 2)[-1] if ids else ""
        out = {"answer": body.strip().split("\n")[0][:200], "citations": ids[:1], "confidence": 0.5, "entities_used": []}
    elif schema and "entities" in json.dumps(schema):
        text = user.split("TEXT:", 1)[-1]
        ents = [{"type": "Date", "text": m} for m in re.findall(r"\d{1,2} [A-Z][a-z]+ 20\d\d", text)]
        ents += [{"type": "Circular", "text": m} for m in re.findall(r"DEO/[A-Z]{3}/\d{4}/\d{3}", text)]
        out = {"entities": ents}
    else:
        out = {"text": "yes"}
    return {"text": json.dumps(out), "token_logprobs": [-0.1] * 5, "top_logprobs": [{"yes": -0.2, "no": -1.8}], "seconds": 0.01, "completion_tokens": 5,
            "prompt_tokens": len(user) // 4, "tokens_per_second": 500.0}
