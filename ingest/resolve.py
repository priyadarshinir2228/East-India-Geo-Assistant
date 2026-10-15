"""Normalisation and resolution: turn mentions into entities with deterministic IDs.

Schools are linked to GeoServer features (osm_id) by string similarity on normalised names,
with an acronym rule (SXCS, DPS) and a location tie-break. Variants that link to the same
feature group merge into one entity. The threshold is chosen in evalsuite/eval_resolution.py.
"""
import math
import re
from collections import defaultdict

from rapidfuzz import fuzz

from common.geo import wfs_layer
from ingest.schema import BOARD_ALIASES, parse_date, parse_quantity, rule_id, slug

INITIALS_RULE = True  # the Task 8 fix: "K.K. Hindu Academy" -> "Dum Dum Krishna Kumar Hindu Academy"
LINK_THRESHOLD = 88  # 85-90 tie in evalsuite/results/task2_resolution.md; 88 sits mid-plateau
PLACE_WORDS = {"kolkata", "darjeeling", "howrah", "main", "building"}
SMALL_WORDS = {"of", "the", "and", "for"}
ABBREV = {"st": "saint", "mt": "mount", "govt": "government", "rkm": "ramakrishna mission"}


def norm_name(s):
    s = s.lower().replace("’", "'").replace("'s", "s").replace("'", "")
    s = re.sub(r"\([^)]*\)", " ", s)          # drop bracketed parts like "(H.S.)"
    s = re.sub(r"\b([a-z])\.(?=[a-z]\.)", r"\1", s)  # K.K. -> kk.
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    words = [ABBREV.get(w, w) for w in s.split() if w not in PLACE_WORDS]
    return " ".join(words)


def acronym(n):
    return "".join(w[0] for w in n.split() if w not in SMALL_WORDS)


GENERIC = {"school", "high", "primary", "middle", "secondary", "government", "public", "girls", "boys", "english",
           "medium", "free", "academy", "institution", "vidyalaya", "group", "schools"}


def collapse_initials(mention_norm, feature_norm):
    """If the mention has a short all-letter token (e.g. "kk" from "K.K.") and the feature has consecutive
    words with those initials ("krishna kumar"), rewrite the feature with the token so the names line up."""
    fw = feature_norm.split()
    for t in mention_norm.split():
        if 2 <= len(t) <= 3 and t.isalpha() and t not in fw:
            for i in range(len(fw) - len(t) + 1):
                if "".join(w[0] for w in fw[i:i + len(t)]) == t:
                    return " ".join(fw[:i] + [t] + fw[i + len(t):])
    return feature_norm


def name_score(mention, feature):
    """0-100 similarity between two normalised names.

    ratio / token_sort_ratio: edit-distance similarity (handles spelling variants like Loreto/Loretto).
    Shortened names ("Bethune School" for "Bethune Collegiate School") get 95% of token_set_ratio,
    but only when every distinctive word of the mention appears in the feature name; otherwise a
    longer mention ("Kendriya Vidyalaya Salt Lake") would wrongly match a shorter feature.
    """
    a, b0 = norm_name(mention), norm_name(feature)
    if not a or not b0:
        return 0.0
    b = collapse_initials(a, b0) if INITIALS_RULE else b0
    ta, tb = set(a.split()) - GENERIC, set(b.split()) - GENERIC
    if not tb:  # all-generic names ("School", "Government Boys High School") only match exactly
        return 100.0 if a == b else 0.0
    score = max(fuzz.ratio(a, b), fuzz.token_sort_ratio(a, b))
    if ta and ta <= set(b.split()):
        score = max(score, 0.95 * fuzz.token_set_ratio(a, b))
    wa, wb = set(a.split()), set(b.split())
    if ("boys" in wa and "girls" in wb) or ("girls" in wa and "boys" in wb):
        score *= 0.8  # a boys' school is never the girls' school next door
    first = a.split()[0]
    if len(first) >= 3 and first == acronym(b0):           # "dps rajarhat" vs "delhi public school"
        score = max(score, 92.0)
    if a.replace(" ", "") == acronym(b0) and len(a) >= 3:  # "sxcs"
        score = max(score, 95.0)
    return float(score)


def _haversine_m(lon1, lat1, lon2, lat2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _centroid(geom):
    ring = geom["coordinates"][0][0] if geom["type"] == "MultiPolygon" else geom["coordinates"][0]
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def school_groups():
    """Group same-name buildings that lie within 1 km of each other into one school."""
    groups = []
    for f in wfs_layer("schools")["features"]:
        p = f["properties"]
        if not p.get("name"):
            continue
        lon, lat = _centroid(f["geometry"])
        n = norm_name(p["name"])
        g = next((g for g in groups if g["norm"] == n and _haversine_m(lon, lat, g["lon"], g["lat"]) < 1000), None)
        if g is None:
            g = {"norm": n, "name": p["name"], "osm_ids": [], "lon": lon, "lat": lat,
                 "board": p.get("board"), "seats": p.get("seats"), "cutoff_marks": p.get("cutoff_marks")}
            groups.append(g)
        g["osm_ids"].append(p["osm_id"])
        if len(p["name"]) < len(g["name"]):  # the shortest spelling names the group
            g["name"] = p["name"]
        g["board"] = g["board"] or p.get("board")
        g["seats"] = g["seats"] or p.get("seats")
        g["cutoff_marks"] = g["cutoff_marks"] or p.get("cutoff_marks")
    for g in groups:
        g["osm_ids"].sort(key=int)
        g["entity_id"] = "SCH-" + g["osm_ids"][0]
    return groups


def link_school(text, groups, near=None, threshold=LINK_THRESHOLD):
    """Return (group or None, score). `near` = (lon, lat) of the document's context for tie-breaks."""
    scored = sorted(((name_score(text, g["name"]), g) for g in groups), key=lambda x: -x[0])
    if not scored or scored[0][0] < threshold:
        return None, (scored[0][0] if scored else 0.0)
    best = scored[0][0]
    tied = [g for s, g in scored if s >= best - 2]
    if near and len(tied) > 1:
        tied.sort(key=lambda g: _haversine_m(near[0], near[1], g["lon"], g["lat"]))
    else:
        tied.sort(key=lambda g: int(g["osm_ids"][0]))
    return tied[0], best


class Resolver:
    def __init__(self):
        self.groups = school_groups()
        self.boards = {a.lower(): bid for bid, al in BOARD_ALIASES.items() for a in al}
        self.roads, self.road_names = {}, {}
        for f in wfs_layer("roads")["features"]:
            p = f["properties"]
            self.road_names[p["road_id"]] = p["name"]
            for n in [p["name"]] + [a.strip() for a in (p.get("alt_names") or "").split(";") if a.strip()]:
                self.roads[n.lower()] = p["road_id"]
        self.localities = {}
        self.loc_points = {}
        for f in wfs_layer("landuse")["features"]:
            p = f["properties"]
            self.localities[p["name"].lower()] = p["locality_id"]
            self.loc_points[p["locality_id"]] = (p["name"], _centroid(f["geometry"]))

    def entity_key(self, m, near=None):
        """Map one mention to (entity_id, canonical_name, attributes)."""
        t, s = m["type"], m["text"].strip()
        if t == "School":
            g, score = link_school(s, self.groups, near)
            if g:
                return g["entity_id"], g["name"], {
                    "osm_ids": g["osm_ids"], "location": {"lat": g["lat"], "lon": g["lon"]}, "board": g["board"],
                    "seats": g["seats"], "cutoff_marks": g["cutoff_marks"], "link_score": score}
            return "SCH-X-" + slug(norm_name(s) or s), s, {"unlinked": True, "link_score": score}
        if t == "Board":
            bid = self.boards.get(s.lower(), "BRD-" + slug(s))
            return bid, BOARD_ALIASES.get(bid, [s])[1] if bid in BOARD_ALIASES else s, {"short_name": BOARD_ALIASES.get(bid, [s])[0]}
        if t == "Road":
            rid = self.roads.get(s.lower(), "RD-" + slug(s))
            return rid, self.road_names.get(rid, s), {}
        if t == "Locality":
            lid = self.localities.get(s.lower(), "LOC-" + slug(s))
            return lid, self.loc_points.get(lid, (s,))[0], {}
        if t == "Circular":
            num = re.sub(r"\s+", "", s).upper()
            return "CIR-" + num.replace("/", "-"), num, {"number": num}
        if t == "Date":
            iso = parse_date(s)
            return (f"DATE-{iso}", iso, {"date": iso}) if iso else ("DATE-X-" + slug(s), s, {})
        if t == "Quantity":
            kind, v = parse_quantity(s)
            return f"QTY-{kind}-{v}", s, {"kind": kind, "value": v}
        if t == "Rule":
            return rule_id(s), s, {}
        return f"{t.upper()}-{slug(s)}", s, {}

    def resolve(self, mentions, doc_context=None):
        """mentions: dicts with type/text/doc_id/chunk_id/start/end. doc_context: doc_id -> (lon, lat).
        Returns (entities by id, mention->entity id list)."""
        ents, assigned = {}, []
        for m in mentions:
            eid, canon, attrs = self.entity_key(m, (doc_context or {}).get(m["doc_id"]))
            e = ents.setdefault(eid, {"entity_id": eid, "type": m["type"], "canonical_name": canon,
                                      "aliases": set(), "mentions": [], "attributes": {}})
            e["aliases"].add(m["text"].strip())
            e["mentions"].append({k: m[k] for k in ("doc_id", "chunk_id", "start", "end", "text")})
            for k, v in attrs.items():
                if v is not None and k not in ("link_score", "unlinked"):
                    e["attributes"][k] = v
            if attrs.get("unlinked"):
                e["unlinked"] = True
            assigned.append(eid)
        for e in ents.values():
            e["aliases"] = sorted(e["aliases"])
            e["mentions"].sort(key=lambda x: (x["doc_id"], x["start"]))
        return ents, assigned

    def doc_context(self, mentions):
        """A document's context point = centre of the localities it mentions (for school tie-breaks)."""
        pts = defaultdict(list)
        for m in mentions:
            if m["type"] == "Locality":
                lid = self.localities.get(m["text"].lower())
                if lid:
                    pts[m["doc_id"]].append(self.loc_points[lid][1])
        return {d: (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps)) for d, ps in pts.items()}
