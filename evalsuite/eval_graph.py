"""Task 4.4, 4.5, 4.7: traversal demo, graph measures, one benefit and one noise example."""
from common import config
from common.io import write_md_table
from evalsuite import qrels as Q
from retrieve import graph, search



def ranked_ids(lst):
    return [d["chunk_id"] for d in lst]


def main():
    G = graph.load_graph()
    m = graph.graph_measures(G)
    rows = [["nodes", m["nodes"]], ["edges", m["edges"]], ["connected components (undirected)", m["components"]]]
    rows += [[f"degree #{i + 1}", f"{graph.name_of(n)} ({n}): {d}"] for i, (n, d) in enumerate(m["top_degree"])]
    rows += [[f"PageRank #{i + 1}", f"{graph.name_of(n)}: {p:.4f}"] for i, (n, p) in enumerate(m["top_pagerank"])]
    rows += [[f"edges of type {t}", c] for t, c in m["edge_types"].items()]

    hare = "SCH-360501161"
    lines = ["**Traversal from Hare School (2 hops, max 25 nodes expanded per step)**", ""]
    for node, info in sorted(graph.neighbours(hare, 2).items(), key=lambda kv: (kv[1]["hops"], -kv[1]["weight"]))[:15]:
        lines.append(f"- hop {info['hops']}, weight {info['weight']:.2f}: {graph.name_of(node)} via {graph.path_str(info['path']) or '(start)'}")
    # pick the clearest benefit and the clearest noise case among all judged queries
    cases = []
    for q in Q.load("retrieval_judgments.jsonl"):
        plain, exp = ranked_ids(search.hybrid(q["query"], 10)), ranked_ids(search.graph_hybrid(q["query"], 10))
        rel = lambda ids, qr=q["qrels"]: [c for c in ids if qr.get(c, 0) >= 1]  # noqa: E731
        gain = len(set(rel(exp)) - set(rel(plain)))
        noise = len(set(exp) - set(plain) - set(rel(exp)))
        cases.append((gain, noise, q, plain, exp, rel))
    benefit = max(cases, key=lambda c: (c[0], -c[1]))
    noisy = max(cases, key=lambda c: (c[1], -c[0]))
    for title, (_, _, q, plain, exp, rel) in [("Benefit", benefit), ("Noise", noisy)]:
        q = q["query"]
        lines += ["", f"**{title}: {q}**", "",
                  f"- relevant in hybrid top-10: {len(rel(plain))} {rel(plain)}",
                  f"- relevant in graph-expanded top-10: {len(rel(exp))} {rel(exp)}",
                  f"- only found with the graph: {sorted(set(rel(exp)) - set(rel(plain)))}",
                  f"- added by the graph but not relevant: {sorted(set(exp) - set(plain) - set(rel(exp)))}"]
    lines += ["", "Noise control: path weight is the product of edge weights; paths through hubs (degree > "
              f"{graph.HUB_DEGREE}, e.g. a board linked to dozens of schools) keep only {graph.HUB_PENALTY} of their weight; "
              "paths under 0.3 are dropped; at most 25 nodes are expanded per hop; and the graph list enters RRF with weight "
              f"{search.GRAPH_WEIGHT}, so it can lift but rarely outvote the text evidence."]
    write_md_table(config.RESULTS / "task4_graph.md", "Task 4: graph measures", ["Measure", "Value"], rows, notes="\n".join(lines))


if __name__ == "__main__":
    main()
