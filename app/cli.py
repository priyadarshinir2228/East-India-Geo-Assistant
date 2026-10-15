"""Command-line interface: python -m app.cli "Which circulars apply to the board of Hare School?" """
import sys

from app.pipeline import answer


def show(r):
    print(f"\nQ: {r['question']}\n")
    print(f"ANSWER: {r['answer']}")
    if r.get("refused"):
        print(f"(refused: {r['refused']})")
        return
    print(f"CONFIDENCE: {r['confidence']}  (signals {r['signals']})" + ("  -> ABSTAINED: " + r["abstain_reason"] if r["abstained"] else ""))
    print(f"CITATIONS: {r['citations']}" + (f"  INVALID: {r['invalid_citations']}" if r["invalid_citations"] else ""))
    print("ENTITIES: " + ", ".join(f"{e['name']} ({e['type']})" for e in r["entities"]))
    for p in r["graph_paths"][:3]:
        print(f"GRAPH PATH: {p}")
    print("TOP PASSAGES:")
    for p in r["passages"]:
        print(f"  [{p['chunk_id']}] p.{p['page']} score {p['rerank_score']:.2f}  {p['text'][:90]!r}")
    if r["suspicious_passages"]:
        print(f"UNTRUSTED TEXT FLAGGED (treated as data): {r['suspicious_passages']}")
    print(f"SETTINGS: {r['settings']}\nTIME: {r['total_s']} s")


if __name__ == "__main__":
    show(answer(" ".join(sys.argv[1:]) or "When do Class XI forms open in Kolkata?"))
