"""Detect entities in a question, using the same extractor + resolver as ingestion so IDs line up,
plus every alias already seen in the corpus (e.g. "DPS Rajarhat", "SXCS") from east_india_entities."""
import re

from elasticsearch import helpers

from common import config
from common.es import app_client
from ingest import extract_rules
from ingest.resolve import Resolver

_state = {}
ALIAS_TYPES = ["School", "Board", "Locality", "Road", "Circular"]


def _aliases():
    out = {}
    q = {"query": {"terms": {"type": ALIAS_TYPES}}}
    for h in helpers.scan(app_client(), index=config.ENTITIES_INDEX, query=q,
                          _source=["entity_id", "type", "canonical_name", "aliases", "attributes"]):
        e = h["_source"]
        for a in set(e.get("aliases", [])) | {e["canonical_name"]}:
            if len(a) >= 4 and not e["entity_id"].startswith("SCH-X"):
                out[a.lower()] = e
    return out


def detect(question):
    if not _state:
        _state["gaz"] = extract_rules.Gazetteer()
        _state["res"] = Resolver()
        _state["alias"] = _aliases()
    out = {}
    found = [{**m, "doc_id": "query", "chunk_id": "query"} for m in extract_rules.extract(question, _state["gaz"]) if m["type"] != "Rule"]
    near = _state["res"].doc_context(found).get("query")  # localities in the question break name ties
    for m in found:
        eid, name, attrs = _state["res"].entity_key(m, near)
        out[eid] = {"entity_id": eid, "type": m["type"], "name": name, "text": m["text"], "attributes": attrs}
    ql = question.lower()
    for alias, e in _state["alias"].items():  # corpus aliases the patterns may miss
        if e["entity_id"] not in out and re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", ql):
            out[e["entity_id"]] = {"entity_id": e["entity_id"], "type": e["type"], "name": e["canonical_name"],
                                   "text": alias, "attributes": e.get("attributes", {})}
    return list(out.values())
