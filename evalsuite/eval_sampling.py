"""Task 7.6: answer the 10 dev questions at temperature 0, 0.3 and 0.7, five times each, with the
same retrieved passages, and measure consistency of key facts and citations."""
import re
from collections import Counter

from app import pipeline
from common import config
from common.io import read_jsonl, write_md_table
from evalsuite.metrics import mean

TOP_P, TOP_K = 0.95, 40
FACT_RE = re.compile(r"\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b"
                     r"|DEO/[A-Z]{3}/\d{4}/\d{3}|\b\d+(?:\.\d+)?%?|\b[A-Z][a-z]+(?: [A-Z][a-z']+)+")


def key(obj):
    facts = frozenset(m.lower() for m in FACT_RE.findall(obj["answer"]))
    return facts, frozenset(obj["citations"])


def main():
    dev = [d for d in read_jsonl(config.EVAL_DIR / "dev_questions.jsonl")]
    rows, per_t = [], {}
    for temp in [0.0, 0.3, 0.7]:
        cons_f, cons_c = [], []
        for d in dev:
            if pipeline.safety.screen(d["question"]):
                continue
            rr = pipeline.retrieve_and_rank(d["question"])
            top, facts = rr["ranked"][:5], pipeline.graph_facts(rr["entities"])
            outs = [key(pipeline.generate(d["question"], top, facts, temperature=temp,
                                          top_p=TOP_P if temp else 1.0, top_k=TOP_K, seed=100 + i)[0]) for i in range(5)]
            maj_f = Counter(o[0] for o in outs).most_common(1)[0][0]
            maj_c = Counter(o[1] for o in outs).most_common(1)[0][0]
            cons_f.append(sum(o[0] == maj_f for o in outs) / 5)
            cons_c.append(sum(o[1] == maj_c for o in outs) / 5)
        per_t[temp] = (mean(cons_f), mean(cons_c))
        rows.append([temp, TOP_P if temp else "1.0 (greedy)", TOP_K, f"{mean(cons_f):.2f}", f"{mean(cons_c):.2f}"])
    write_md_table(config.RESULTS / "task7_sampling.md", "Task 7: sampling temperature and consistency (5 runs x 9 questions)",
                   ["Temperature", "top_p", "top_k", "Same key facts as majority", "Same citations as majority"], rows,
                   notes="Recommendation: entity extraction temperature 0 (repeatable IDs and spans); scoring (LLM yes/no) "
                         "temperature 0 (a score must not change between runs); answering temperature 0 for the PoC. Greedy "
                         "decoding picks the most likely token at each step; that makes the output repeatable, not correct: "
                         "if the passages are wrong or the model's most likely continuation is wrong, greedy repeats the "
                         "same mistake every time. The out-of-scope question is refused before generation, so 9 are used.")


if __name__ == "__main__":
    main()
