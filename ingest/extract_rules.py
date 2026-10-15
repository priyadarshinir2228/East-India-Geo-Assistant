"""Non-LLM baseline extractor: regular expressions plus a gazetteer built from GeoServer layers.

Gazetteer sources (read over WFS as rag_geo):
  schools layer  -> school names        roads layer -> road names and alternative names
  landuse layer  -> locality names      boards      -> fixed alias table in ingest/schema.py
"""
import re

from common.geo import wfs_layer
from ingest.schema import BOARD_ALIASES

DATE_RE = re.compile(
    r"\b(?:\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}"
    r"|(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}"
    r"|\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\b")
CIRCULAR_RE = re.compile(r"\bDEO/[A-Z]{3}/\d{4}/\d{3}\b")
QTY_RE = re.compile(r"\b\d+(?: (?:seats|years|days|marks|per cent|km)\b|%)")
SCHOOL_SUFFIX = (r"(?:High School(?: for (?:Boys|Girls))?|School|Academy|Vidyapith|Vidyalaya|Institution|Convent|"
                 r"Collegiate|Vidyamandir|Niketan|Sikshalaya|Group of Schools)")
# A run of capitalised words (allowing St. / K.K. / apostrophes) ending in a school-type word
# tokens: "St.", initials like "K.K." / "B.E.", or a capitalised word; separated by single spaces only
_TOKEN = r"(?:St\.|Mt\.|(?:[A-Z]\.){1,3}|[A-Z][\w'’]*)"
SCHOOL_RE = re.compile(r"\b(?:" + _TOKEN + r" ){0,6}" + SCHOOL_SUFFIX + r"\b")
ROAD_RE = re.compile(r"\b(?:" + _TOKEN + r" ){1,3}(?:Road|Avenue|Sarani)\b")
GENERIC = {"school", "high", "primary", "middle", "secondary", "government", "govt", "public", "girls", "boys", "the",
           "english", "medium", "free", "building", "main", "stage", "library", "canteen", "block", "auditorium", "lab", "science"}
LIST_MARK = re.compile(r"^\s*(?:-|\d+\.)\s+")
ACRONYM_RE = re.compile(r"\b([A-Z]{3,5})\b(?: ([A-Z][a-z]+))?")
RULE_CUES = re.compile(r"\b(must|shall|minimum|maximum|reserved|at least|up to|should|relaxation)\b", re.I)
SENT_RE = re.compile(r"[^.\n]+(?:\.(?!\d)|$)", re.M)
STOP_LEADS = {"The", "This", "Schools", "School", "All", "Students", "Where", "Parents", "Admission", "Heads", "Because"}


def _norm(s):
    return re.sub(r"[^a-z0-9 ]+", "", s.lower().replace("’", "'")).strip()


class Gazetteer:
    def __init__(self):
        schools = wfs_layer("schools")["features"]
        roads = wfs_layer("roads")["features"]
        landuse = wfs_layer("landuse")["features"]
        names = {f["properties"]["name"] for f in schools if f["properties"].get("name")}
        # skip generic names ("School", "primary school", "Library / Canteen"): they would match everywhere
        self.school_names = sorted((n for n in names if len(_norm(n).split()) >= 2 and set(_norm(n).split()) - GENERIC),
                                   key=len, reverse=True)
        self.roads = {}
        for f in roads:
            p = f["properties"]
            for n in [p["name"]] + [a.strip() for a in (p.get("alt_names") or "").split(";") if a.strip()]:
                self.roads[n] = p["road_id"]
        self.localities = {f["properties"]["name"]: f["properties"]["locality_id"] for f in landuse}
        self.boards = {a: bid for bid, al in BOARD_ALIASES.items() for a in al}
        # acronyms of school names ("SXCS" = St Xavier's Collegiate School, "DPS" = Delhi Public School)
        self.acronyms = set()
        for n in self.school_names:
            words = [w for w in re.sub(r"[^A-Za-z ]+", " ", re.sub(r"['’]s\b", "s", n)).split() if w.lower() not in {"of", "the", "and", "for"}]
            if len(words) >= 3:
                self.acronyms.add("".join(w[0] for w in words).upper())
        self.acronyms -= set(self.boards) | {"DEO", "EWS", "RTE", "OSM", "IPL"}


def _find_all(text, phrase, ignore_case=False):
    flags = re.I if ignore_case else 0
    return [(m.start(), m.end()) for m in re.finditer(r"(?<![\w])" + re.escape(phrase) + r"(?![\w])", text, flags)]


def extract(text, gaz: Gazetteer):
    """Return mentions [{type, start, end, text}] found in text."""
    out = []
    add = lambda t, s, e: out.append({"type": t, "start": s, "end": e, "text": text[s:e]})  # noqa: E731
    for m in DATE_RE.finditer(text):
        add("Date", m.start(), m.end())
    for m in CIRCULAR_RE.finditer(text):
        add("Circular", m.start(), m.end())
    for m in QTY_RE.finditer(text):
        add("Quantity", m.start(), m.end())
    # table cells "| 120 |" in the cut-off table are seat counts
    for m in re.finditer(r"(?<=\| )\d{2,3}(?= \|)", text):
        add("Quantity", m.start(), m.end())
    for alias, _ in sorted(gaz.boards.items(), key=lambda kv: -len(kv[0])):
        for s, e in _find_all(text, alias):
            add("Board", s, e)
    for name in gaz.school_names:  # exact gazetteer hits (case-insensitive)
        if len(name) >= 6:
            for s, e in _find_all(text, name, ignore_case=True):
                add("School", s, e)
    for m in SCHOOL_RE.finditer(text):  # pattern hits catch spelling variants not in the gazetteer
        s = m.start()
        words = m.group().split()
        while words and words[0] in STOP_LEADS:  # drop sentence-initial words like "The"
            s += len(words[0]) + 1
            words = words[1:]
        if len(words) >= 2:
            add("School", s, m.end())
    for m in ACRONYM_RE.finditer(text):  # "SXCS", "DPS Rajarhat"
        if m.group(1) in gaz.acronyms:
            end = m.end(2) if m.group(2) and m.group(2) in gaz.localities else m.end(1)
            add("School", m.start(1), end)
    for name in list(gaz.localities) + list(gaz.roads):
        for s, e in _find_all(text, name):
            before = text[max(0, s - 7):s].lower()
            is_loc, is_road = name in gaz.localities, name in gaz.roads
            if is_loc and is_road:  # "Park Street", "College Street": decide from the preceding word
                is_road = bool(re.search(r"\b(on|along|use|of)\s+$", before))
                is_loc = not is_road
            add("Road" if is_road else "Locality", s, e)
    for m in ROAD_RE.finditer(text):
        add("Road", m.start(), m.end())
    for m in SENT_RE.finditer(text):
        sent = m.group()
        if RULE_CUES.search(sent):
            lm = LIST_MARK.match(sent)
            lead = lm.end() if lm else len(sent) - len(sent.lstrip())
            add("Rule", m.start() + lead, m.end())
    return _dedupe(out)


def _dedupe(ms):
    """Keep one mention per (type, span); among overlapping same-type mentions keep the longest.
    Rules are allowed to contain other entities, so overlap is only resolved within a type."""
    ms = sorted({(m["type"], m["start"], m["end"]): m for m in ms}.values(), key=lambda m: (m["type"], -(m["end"] - m["start"]), m["start"]))
    kept = []
    for m in ms:
        if not any(k["type"] == m["type"] and k["start"] < m["end"] and m["start"] < k["end"] for k in kept):
            kept.append(m)
    # a Road span inside a School span (e.g. "Park Street" inside a school name) is dropped
    schools = [k for k in kept if k["type"] == "School"]
    kept = [k for k in kept if not (k["type"] in ("Road", "Locality") and any(
        s["start"] <= k["start"] and k["end"] <= s["end"] for s in schools))]
    return sorted(kept, key=lambda m: (m["start"], m["type"]))
