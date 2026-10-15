"""End-to-end ingestion (runs as rag_app). Idempotent: deterministic IDs + bulk "index" operations,
so a second run overwrites the same documents and the counts stay the same.

  load -> chunk -> extract entities -> resolve -> relations -> embed -> index
Run: python -m ingest.run_ingest [--extractor rules|llm|hybrid] [--model BAAI/bge-small-en-v1.5]
"""
import argparse
import re
import time
from collections import defaultdict

from elasticsearch import helpers

from common import config
from common.es import app_client
from common.io import write_jsonl
from common.models import get_embedder
from ingest import extract_rules
from ingest.chunking import chunk_document
from ingest.loaders import load_documents
from ingest.relations import build_relations
from ingest.resolve import Resolver
from ingest.schema import parse_date


def extract_all(chunks, extractor):
    gaz = extract_rules.Gazetteer()
    mentions = []
    for c in chunks:
        found = []
        if extractor in ("rules", "hybrid") or c["doc_kind"] == "directory":
            found += extract_rules.extract(c["text"], gaz)
        if extractor in ("llm", "hybrid") and c["doc_kind"] != "directory":  # directory pages: rules only
            from ingest import extract_llm
            llm_found, _ = extract_llm.extract(c["text"])
            seen = {(m["type"], m["start"], m["end"]) for m in found}
            found += [m for m in llm_found if (m["type"], m["start"], m["end"]) not in seen]
        for m in found:  # chunk offsets -> document offsets
            mentions.append({**m, "start": m["start"] + c["start"], "end": m["end"] + c["start"],
                             "doc_id": c["doc_id"], "chunk_id": c["chunk_id"]})
    # overlapping chunks see the same text twice: keep one mention per (doc, type, span)
    uniq = {(m["doc_id"], m["type"], m["start"], m["end"]): m for m in mentions}
    return sorted(uniq.values(), key=lambda m: (m["doc_id"], m["start"]))


def chunk_metadata(chunks, entities, docs):
    by_chunk = defaultdict(set)
    for e in entities.values():
        for m in e["mentions"]:
            by_chunk[m["chunk_id"]].add(e["entity_id"])
    issued = {}
    for d, doc in docs.items():
        m = re.search(r"^(?:Date|Issued)\s*:\s*(.+)$", doc["text"], re.M)
        issued[d] = parse_date(m.group(1)) if m else None
    for c in chunks:
        ids = sorted(by_chunk[c["chunk_id"]])
        c["entity_ids"] = ids
        c["school_ids"] = [i for i in ids if i.startswith("SCH-")]
        boards = {i for i in ids if i.startswith("BRD-")}
        boards |= {"BRD-" + entities[i]["attributes"]["board"] for i in c["school_ids"] if entities[i]["attributes"].get("board")}
        c["boards"] = sorted(boards)
        c["issued_date"] = issued.get(c["doc_id"])
        locs = [entities[i]["attributes"]["location"] for i in c["school_ids"] if "location" in entities[i]["attributes"]]
        c["location"] = locs or None


def bulk_index(es, index, rows, id_field):
    actions = ({"_op_type": "index", "_index": index, "_id": r[id_field], "_source": r} for r in rows)
    # refresh="wait_for": return once the documents are searchable (rag_app may not force a refresh)
    ok, errors = helpers.bulk(es, actions, raise_on_error=False, chunk_size=200, refresh="wait_for")
    # remove documents left over from an earlier run with different chunking or extraction
    es.delete_by_query(index=index, query={"bool": {"must_not": {"ids": {"values": [r[id_field] for r in rows]}}}},
                       conflicts="proceed")
    time.sleep(1.5)  # one refresh interval, so the count below sees the deletions
    return ok, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractor", default="rules", choices=["rules", "llm", "hybrid"])
    ap.add_argument("--model", default=config.EMBED_MODEL)
    ap.add_argument("--skip-index", action="store_true")
    a = ap.parse_args()
    t0 = time.perf_counter()
    docs = {d["doc_id"]: d for d in load_documents()}
    chunks = [c for d in docs.values() for c in chunk_document(d)]
    print(f"{len(docs)} documents -> {len(chunks)} chunks")

    mentions = extract_all(chunks, a.extractor)
    resolver = Resolver()
    entities, _ = resolver.resolve(mentions, resolver.doc_context(mentions))
    unlinked = sorted({e["canonical_name"] for e in entities.values() if e.get("unlinked")})
    print(f"{len(mentions)} mentions -> {len(entities)} entities; unlinked schools: {unlinked}")

    relations = build_relations(entities, chunks, docs)
    print(f"{len(relations)} relations")
    chunk_metadata(chunks, entities, docs)

    emb = get_embedder(a.model)
    t = time.perf_counter()
    vecs = emb.passages([c["title"] + "\n" + c["text"] for c in chunks])
    print(f"embedded {len(chunks)} chunks with {emb.name} ({emb.dims} dims) in {time.perf_counter() - t:.1f}s")
    for c, v in zip(chunks, vecs):
        c["embedding"] = c["embedding_f32"] = [round(float(x), 6) for x in v]

    config.WORK.mkdir(parents=True, exist_ok=True)
    write_jsonl(config.WORK / "chunks.jsonl", [{k: v for k, v in c.items() if not k.startswith("embedding")} for c in chunks])
    write_jsonl(config.WORK / "mentions.jsonl", mentions)
    ent_rows = [{k: v for k, v in e.items() if k != "unlinked"} for e in entities.values()]
    write_jsonl(config.WORK / "entities.jsonl", ent_rows)
    write_jsonl(config.WORK / "relations.jsonl", relations)
    (config.WORK / "unlinked_schools.txt").write_text("\n".join(unlinked) + "\n", encoding="utf-8")
    if a.skip_index:
        return

    es = app_client()  # rag_app only from here on
    for index, rows, key in [(config.CHUNKS_INDEX, chunks, "chunk_id"), (config.ENTITIES_INDEX, ent_rows, "entity_id"),
                             (config.RELATIONS_INDEX, relations, "relation_id")]:
        ok, errors = bulk_index(es, index, rows, key)
        count = es.count(index=index)["count"]
        print(f"{index}: indexed {ok}, errors {len(errors) if isinstance(errors, list) else errors}, count now {count}")
    print(f"done in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
