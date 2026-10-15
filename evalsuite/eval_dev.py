"""Task 8.5: run the 10 dev questions end to end and score answers and citations."""
import json
import re

from app import pipeline
from common import config
from common.io import read_jsonl, write_md_table


def norm(s):
    return re.sub(r"[^a-z0-9% ]+", " ", s.lower())


def main():
    dev = read_jsonl(config.EVAL_DIR / "dev_questions.jsonl")
    rows, full = [], []
    n_ok = n_cite = n_cite_total = 0
    for d in dev:
        r = pipeline.answer(d["question"])
        if d["answerable"]:
            ok = (not r["abstained"]) and not r.get("refused") and all(norm(f) in norm(r["answer"]) for f in d["key_facts"])
            cited_docs = {c.split(":")[0] for c in r["citations"]}
            cite_ok = not r.get("invalid_citations") and (bool(cited_docs & set(d["gold_docs"])) or "geoserver" in r["citations"])
            n_cite_total += 1
            n_cite += cite_ok
        else:
            ok = bool(r["abstained"] or r.get("refused"))
            cite_ok = None
        n_ok += ok
        rows.append([d["id"], d["question"], ", ".join(e["name"] for e in r["entities"]) or "-",
                     " ".join(p["chunk_id"] for p in r["passages"][:3]) or "-", r["confidence"] if r["confidence"] is not None else "-",
                     r["answer"].replace("|", "/")[:160], "yes" if ok else "NO", "-" if cite_ok is None else ("yes" if cite_ok else "NO")])
        full.append(r)
    (config.RESULTS / "task8_dev_answers.json").write_text(json.dumps(full, indent=1, ensure_ascii=False))
    write_md_table(config.RESULTS / "task8_dev.md", "Task 8: development questions end to end",
                   ["ID", "Question", "Entities", "Top passages", "Confidence", "Answer", "Answer correct", "Citations correct"], rows,
                   notes=f"Answer accuracy {n_ok}/{len(dev)}; citation correctness {n_cite}/{n_cite_total} answerable questions. "
                         "Unanswerable questions count as correct when the assistant abstains or refuses.")


if __name__ == "__main__":
    main()
