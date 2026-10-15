"""Build typed relations between entities (Task 4).

Each edge: source_id, target_id, type, weight in [0, 1], evidence (a chunk ID or "geoserver").
How weights are set:
  - Each piece of evidence has a base confidence by method: GeoServer attribute or geometry 1.0
    (or distance-scaled), explicit wording ("Applies to:", "supersedes") 0.95, a mention in a
    circular 0.9, a same-sentence pattern in a note 0.8, an inference (rule inherits the board of
    its circular) 0.7, date/subject heuristic 0.6.
  - Independent evidence for the same edge is combined with noisy-OR: w = 1 - prod(1 - w_i),
    so two weak sources give more confidence than either alone but never exceed 1.
"""
import hashlib
import re
from collections import defaultdict

import geopandas as gpd
from shapely.geometry import shape

from common.geo import wfs_layer

PROJECTED_CRS = 32646  # required by the assessment (UTM 46N); scale error under ~1% here
NEAR_M = 300


def rel_id(src, typ, dst):
    return hashlib.sha1(f"{src}|{typ}|{dst}".encode()).hexdigest()[:16]


class EdgeBuilder:
    def __init__(self):
        self.ev = defaultdict(list)  # (src, type, dst) -> [(weight, evidence, method, extra)]

    def add(self, src, typ, dst, w, evidence, method, **extra):
        if src != dst:
            self.ev[(src, typ, dst)].append((w, evidence, method, extra))

    def records(self):
        out = []
        for (src, typ, dst), evs in self.ev.items():
            p_none = 1.0
            for w, *_ in evs:
                p_none *= 1 - w
            best = max(evs, key=lambda e: e[0])
            rec = {"relation_id": rel_id(src, typ, dst), "source_id": src, "target_id": dst, "type": typ,
                   "weight": round(1 - p_none, 4), "evidence": best[1], "method": best[2],
                   "evidence_text": "; ".join(sorted({f"{m}:{e}" for _, e, m, _ in evs}))}
            if "distance_m" in best[3]:
                rec["distance_m"] = round(best[3]["distance_m"], 1)
            out.append(rec)
        return sorted(out, key=lambda r: r["relation_id"])


def _sentence_of(text, pos):
    s = max(text.rfind(". ", 0, pos), text.rfind("\n", 0, pos)) + 1
    e_candidates = [i for i in (text.find(". ", pos), text.find("\n", pos)) if i >= 0]
    return s, (min(e_candidates) if e_candidates else len(text))


def build_relations(entities, chunks, docs):
    """entities: id -> entity dict (with mentions); chunks: list; docs: doc_id -> {text, kind, title}."""
    E = EdgeBuilder()
    by_doc = defaultdict(list)  # doc_id -> [(start, end, entity_id, type, chunk_id)]
    for e in entities.values():
        for m in e["mentions"]:
            by_doc[m["doc_id"]].append((m["start"], m["end"], e["entity_id"], e["type"], m["chunk_id"]))
    for v in by_doc.values():
        v.sort()

    # the circular each document *is* (the one named in its title line)
    doc_circular = {}
    for d, ms in by_doc.items():
        title_end = docs[d]["text"].find("\n")
        own = [m for m in ms if m[3] == "Circular" and m[0] < title_end]
        if own:
            doc_circular[d] = own[0][2]

    # --- text-based relations ---
    for d, ms in by_doc.items():
        text = docs[d]["text"]
        circ = doc_circular.get(d)
        applies_boards = []
        for s, e, eid, typ, cid in ms:
            line_start = text.rfind("\n", 0, s) + 1
            line = text[line_start:text.find("\n", s) if text.find("\n", s) >= 0 else len(text)]
            if circ and typ == "Board" and line.startswith("Applies to:"):
                E.add(circ, "applies_to", eid, 0.95, cid, "applies_to_line")
                applies_boards.append(eid)
            if circ and typ == "School":
                E.add(circ, "mentions", eid, 0.9, cid, "mention_in_circular")
            if circ and typ == "Circular" and eid != circ and re.search(r"supersedes\s+circular\s*$", text[max(0, s - 40):s], re.I):
                E.add(circ, "supersedes", eid, 0.95, cid, "supersedes_wording")
        for s, e, eid, typ, cid in ms:
            if typ == "Rule":
                for b in applies_boards:  # a rule in a circular inherits the circular's boards
                    E.add(eid, "applies_to", b, 0.7, cid, "rule_in_circular")
                if circ:
                    E.add(circ, "states", eid, 0.9, cid, "rule_in_circular")
        # same-sentence patterns in notes and guidelines
        for s, e, eid, typ, cid in ms:
            if typ != "School":
                continue
            ss, se = _sentence_of(text, s)
            window = [(m[2], m[3]) for m in ms if m[0] >= ss and m[1] <= se + 60 and m[2] != eid]
            for oid, otyp in window:
                if otyp == "Board" and re.search(r"\bschool\b|Board:", text[ss:se + 60]):
                    E.add(eid, "affiliated_with", oid, 0.8, cid, "same_sentence")
                if otyp == "Locality":
                    E.add(eid, "located_in", oid, 0.8, cid, "same_sentence")
                if otyp == "Road" and re.search(r"located on|Nearest main road", text[ss:se + 60]):
                    E.add(eid, "near", oid, 0.8, cid, "same_sentence")
        # school notes put board / locality / road on separate lines of the same note
        if docs[d]["kind"] == "school_note":
            schools = [m for m in ms if m[3] == "School"]
            if schools:
                sid, cid0 = schools[0][2], schools[0][4]
                for s, e, eid, typ, cid in ms:
                    if typ == "Board":
                        E.add(sid, "affiliated_with", eid, 0.8, cid, "school_note")
                    elif typ == "Locality":
                        E.add(sid, "located_in", eid, 0.8, cid, "school_note")
                    elif typ == "Road":
                        E.add(sid, "near", eid, 0.8, cid, "school_note")

    # --- supersedes by dates and subject (weaker heuristic) ---
    circ_info = {}
    for d, cid in doc_circular.items():
        m = re.search(r"^Date: (.+)$", docs[d]["text"], re.M)
        subj = re.search(r"^Subject: (.+)$", docs[d]["text"], re.M)
        date_ent = next((x[2] for x in by_doc[d] if x[3] == "Date" and m and m.start() <= x[0] <= m.end()), None)
        if date_ent and subj:
            words = set(re.findall(r"[a-z]+", subj.group(1).lower())) - {"revised", "and", "the", "of", "for", "in"}
            office = cid.split("-")[2]
            circ_info[cid] = (date_ent[5:], words, office)
    for a, (da, wa, oa) in circ_info.items():
        for b, (db, wb, ob) in circ_info.items():
            overlap = len(wa & wb) / max(1, min(len(wa), len(wb)))
            if a != b and oa == ob and da > db and overlap >= 0.75:
                E.add(a, "supersedes", b, 0.6, "dates_and_subject", "date_subject_heuristic")

    # --- GeoServer-based relations ---
    schools = {eid: e for eid, e in entities.items() if e["type"] == "School" and "location" in e["attributes"]}
    for eid, e in schools.items():
        board_short = e["attributes"].get("board")
        if board_short:
            E.add(eid, "affiliated_with", "BRD-" + board_short, 1.0, "geoserver", "layer_attribute")
    if schools:
        pts = gpd.GeoDataFrame({"eid": list(schools)}, geometry=gpd.points_from_xy(
            [schools[s]["attributes"]["location"]["lon"] for s in schools],
            [schools[s]["attributes"]["location"]["lat"] for s in schools]), crs=4326).to_crs(PROJECTED_CRS)
        roads = gpd.GeoDataFrame.from_features(wfs_layer("roads")["features"], crs=4326).to_crs(PROJECTED_CRS)
        land = gpd.GeoDataFrame.from_features(wfs_layer("landuse")["features"], crs=4326).to_crs(PROJECTED_CRS)
        for p in pts.itertuples():
            for r in roads.itertuples():
                dist = p.geometry.distance(r.geometry)  # metres in the projected CRS
                if dist <= NEAR_M:
                    E.add(p.eid, "near", r.road_id, 1 - 0.5 * dist / NEAR_M, "geoserver", "distance_epsg32646", distance_m=dist)
            for lu in land.itertuples():
                if lu.geometry.contains(p.geometry):
                    E.add(p.eid, "located_in", lu.locality_id, 1.0, "geoserver", "point_in_landuse")
    return E.records()


def geometry_from_geojson(f):
    return shape(f["geometry"])
