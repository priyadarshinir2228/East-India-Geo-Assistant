"""Entity schema shared by both extractors, the resolver and the index."""
import hashlib
import re

ENTITY_TYPES = ["School", "Board", "Circular", "Rule", "Locality", "Road", "Date", "Quantity"]

TYPE_DEFINITIONS = {
    "School": "a named school, e.g. 'Hare School', 'SXCS', 'DPS Rajarhat'",
    "Board": "an examination board or council, e.g. 'WBBSE', 'CBSE', 'Council for the Indian School Certificate Examinations'",
    "Circular": "a circular number such as 'DEO/KOL/2026/014'",
    "Rule": "one whole sentence that states an admission rule (an obligation, limit or reservation)",
    "Locality": "a neighbourhood or area of a town, e.g. 'Dum Dum', 'Chowrasta'",
    "Road": "a named road or street when used as a road, e.g. 'Jessore Road', 'Hill Cart Road'",
    "Date": "a calendar date, e.g. '25 May 2026', '10/02/2026'",
    "Quantity": "a number with a unit: seats, marks or percentages, ages in years, days, distances",
}

# JSON schema the LLM output must satisfy (also passed to llama-server as a grammar)
LLM_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"entities": {"type": "array", "items": {
        "type": "object",
        "properties": {"type": {"type": "string", "enum": ENTITY_TYPES},
                       "text": {"type": "string", "minLength": 1, "maxLength": 300}},
        "required": ["type", "text"]}}},
    "required": ["entities"],
}

BOARD_ALIASES = {
    "BRD-WBBSE": ["WBBSE", "West Bengal Board of Secondary Education", "West Bengal Board", "Madhyamik board"],
    "BRD-WBCHSE": ["WBCHSE", "West Bengal Council of Higher Secondary Education", "Higher Secondary Council"],
    "BRD-CBSE": ["CBSE", "Central Board of Secondary Education", "Central Board"],
    "BRD-CISCE": ["CISCE", "Council for the Indian School Certificate Examinations", "ICSE", "ICSE board"],
}

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                       "september", "october", "november", "december"], start=1)}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def rule_id(sentence):
    norm = re.sub(r"\s+", " ", sentence.lower()).strip(" .")
    return "RULE-" + hashlib.sha1(norm.encode()).hexdigest()[:10]


def parse_date(text):
    """Return ISO date for '25 May 2026', 'May 25, 2026', '25/05/2026', '2026-05-25'; else None."""
    t = text.strip().lower().replace(",", "")
    m = re.fullmatch(r"(\d{1,2}) ([a-z]+) (\d{4})", t)
    if m and m.group(2) in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"([a-z]+) (\d{1,2}) (\d{4})", t)
    if m and m.group(1) in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", t)
    return t if m else None


def parse_quantity(text):
    """Return (kind, value) for '120 seats', '85%', '25 per cent', '6 years', '30 days', '1 km', '5 marks'."""
    t = text.lower()
    m = re.search(r"(\d+)", t)
    if not m:
        return None, None
    v = int(m.group(1))
    for kind, pat in [("seats", r"seat"), ("age", r"year"), ("days", r"day"), ("distance_km", r"km"),
                      ("marks", r"mark"), ("percent", r"per cent|percent")]:
        if re.search(pat, t):
            return kind, v
    if "%" in t:
        return "marks", v  # bare % in this corpus is a cut-off mark
    return "count", v
