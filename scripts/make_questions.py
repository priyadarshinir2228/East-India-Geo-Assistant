"""Write the evaluation files (synthetic, hand-written questions with graded judgments).

Judgments point at evidence text inside a document: a chunk earns the grade if it contains
the evidence string (see evalsuite/qrels.py). Grades: 2 = answers the question, 1 = related
or partly useful (for example a superseded circular), 0 = not relevant (implicit).
Run: python -m scripts.make_questions
"""
import json

from common import config
from ingest.loaders import load_documents

J = lambda doc, ev, g=2: {"doc_id": doc, "evidence": ev, "grade": g}  # noqa: E731

RETRIEVAL = [
    # id, split, type, query, judgments
    ("q01", "tune", "exact_id", "What does circular DEO/KOL/2026/014 say?",
     [J("circ-kol-2026-014", "now open on 25 May 2026"), J("circ-kol-2025-031", "Online application forms for Class XI admission open on 20 May 2026", 1)]),
    ("q02", "tune", "exact_id", "DEO/DJL/2026/005",
     [J("circ-djl-2026-005", "postponed to 21 March 2026"), J("circ-djl-2026-002", "Admission tests for the hill schools", 1)]),
    ("q03", "tune", "exact_id", "What is the cut-off at Hare School?",
     [J("circ-kol-2026-018", "| Hare School | College Street | 120 | 85% |"), J("note-sch-360501161", "2026 science cut-off is 85%")]),
    ("q04", "tune", "exact_id", "OSM building 637073212",
     [J("dir-kolkata", "OSM building 637073212"), J("note-sch-637073212", "St Xaviers Collegiate is a CISCE school", 1)]),
    ("q05", "tune", "paraphrase", "How old must a child be to join the first standard?",
     [J("circ-kol-2026-004", "The minimum age for Class I is 6 years"), J("guide-admission-2026", "The minimum age for Class I is 6 years")]),
    ("q06", "tune", "paraphrase", "What share of entry places is kept for poor families?",
     [J("circ-kol-2026-012", "25 per cent of entry-level seats are reserved"), J("guide-admission-2026", "25 per cent of entry-level seats are reserved")]),
    ("q07", "tune", "paraphrase", "What happens when more children apply than there are places?",
     [J("circ-kol-2026-012", "decided by a public lottery"), J("guide-admission-2026", "decided by a public lottery")]),
    ("q08", "tune", "paraphrase", "Which papers must parents bring when enrolling a child?",
     [J("circ-kol-2026-007", "Birth certificate issued by the municipality")]),
    ("q09", "tune", "paraphrase", "When can students apply for higher secondary in Kolkata this year?",
     [J("circ-kol-2026-014", "now open on 25 May 2026"), J("circ-kol-2025-031", "Online application forms for Class XI admission open on 20 May 2026", 1)]),
    ("q10", "tune", "multi_hop", "Which circulars apply to the board of Hare School?",
     [J("circ-kol-2026-014", "Applies to: schools affiliated to WBBSE and WBCHSE"), J("circ-kol-2026-018", "Applies to: schools affiliated to WBBSE"),
      J("circ-kol-2026-004", "Applies to: all WBBSE primary sections"), J("circ-kol-2026-007", "Applies to: all schools (WBBSE, CBSE, CISCE)"),
      J("circ-kol-2025-031", "Applies to: schools affiliated to WBBSE and WBCHSE", 1), J("note-sch-360501161", "is a WBBSE school", 1)]),
    ("q11", "tune", "multi_hop", "Which road closure affects the school buses of K.K. Hindu Academy?",
     [J("circ-kol-2026-021", "Jessore Road will be partly closed"), J("note-sch-1035913079", "It is located on Jessore Road", 1)]),
    ("q12", "tune", "multi_hop", "Is the admission test for Loretto Convent still on 14 February?",
     [J("circ-djl-2026-005", "postponed to 21 March 2026"), J("circ-djl-2026-002", "will be held on 14 February 2026", 1)]),
    ("q13", "tune", "multi_hop", "What reservation rule applies to St Xaviers Collegiate?",
     [J("circ-kol-2026-012", "25 per cent of entry-level seats are reserved"), J("note-sch-637073212", "is a CISCE school", 1)]),
    ("q14", "tune", "list", "List the WBBSE schools and their science cut-offs for 2026",
     [J("circ-kol-2026-018", "| Hare School | College Street | 120 | 85% |"), J("circ-kol-2026-018", "| Dum Dum Subhas Nagar High School | Dum Dum | 100 | 50% |")]),
    ("q15", "tune", "list", "Which schools are in Dum Dum?",
     [J("note-sch-1035913079", "is a WBBSE school in Dum Dum"), J("note-sch-358021840", "is a WBBSE school in Dum Dum"),
      J("town-kolkata-north", "Dum Dum lies along Jessore Road", 1), J("circ-kol-2026-021", "School buses for Dum Dum Krishna Kumar Hindu Academy", 1)]),
    ("q16", "tune", "list", "Name the Darjeeling hill schools covered by the admission circular",
     [J("circ-djl-2026-002", "This applies to Loretto Convent"), J("circ-djl-2026-005", "Students of Government Boys High School", 1)]),
    ("q17", "tune", "exact_id", "Maharani Girls' High School seats",
     [J("note-sch-350304682", "100 seats in Class XI")]),
    ("q18", "tune", "paraphrase", "Where can a child living on Hill Cart Road take the admission test?",
     [J("circ-djl-2026-005", "may attend the test at St. Michael's School")]),
    ("q19", "tune", "paraphrase", "Do reserved category students get any relaxation in the cut-off?",
     [J("circ-kol-2026-018", "receive a relaxation of 5 marks")]),
    ("q20", "tune", "list", "Which busy roads need a traffic warden at school gates?",
     [J("guide-geography", "must post a traffic warden at gate times")]),
    ("q21", "holdout", "exact_id", "Circular DEO/KOL/2026/021",
     [J("circ-kol-2026-021", "Jessore Road will be partly closed")]),
    ("q22", "holdout", "exact_id", "What is the Class XI intake of DPS Rajarhat?",
     [J("note-sch-5341865", "200 seats in Class XI")]),
    ("q23", "holdout", "paraphrase", "What is the oldest age allowed for class one admission?",
     [J("circ-kol-2026-004", "The maximum age for Class I is 8 years"), J("guide-admission-2026", "The maximum age for Class I is 8 years")]),
    ("q24", "holdout", "paraphrase", "How long do families have to hand in the leaving certificate from the old school?",
     [J("circ-kol-2026-007", "within 30 days of admission")]),
    ("q25", "holdout", "paraphrase", "Can brothers and sisters of current pupils get priority?",
     [J("circ-kol-2026-007", "siblings of current students")]),
    ("q26", "holdout", "multi_hop", "Which circulars apply to the board of Mount Hermon School?",
     [J("circ-kol-2026-012", "Applies to: schools affiliated to CBSE and CISCE"), J("circ-kol-2026-007", "Applies to: all schools (WBBSE, CBSE, CISCE)"),
      J("circ-djl-2026-005", "Applies to: hill schools affiliated to WBBSE and CISCE"), J("circ-djl-2026-002", "Applies to: hill schools affiliated to WBBSE and CISCE", 1),
      J("note-sch-348917732", "Board: CISCE", 1)]),
    ("q27", "holdout", "multi_hop", "What is the latest Class XI application deadline for Baranagar RKM High School?",
     [J("circ-kol-2026-014", "close on 10 June 2026"), J("circ-kol-2025-031", "Baranagar RKM High School must display", 1)]),
    ("q28", "holdout", "list", "Which schools must follow the EWS lottery rule in Kolkata?",
     [J("circ-kol-2026-012", "This circular applies in particular to Delhi Public School")]),
    ("q29", "holdout", "paraphrase", "Which stream must get at least 40 per cent of Class XI seats?",
     [J("guide-xi-streams", "At least 40 per cent of Class XI seats")]),
    ("q30", "holdout", "paraphrase", "Can a Higher Secondary Council school add vocational courses?",
     [J("guide-xi-streams", "may add a vocational stream with permission")]),
]

# Calibration: success = top reranked passage has grade >= 1. Unanswerable questions have no judgments.
CALIBRATION = [
    ("c01", "When does the Class XI merit list come out?", [J("circ-kol-2026-014", "merit list will be published on 20 June 2026"), J("circ-kol-2025-031", "merit list will be published on 15 June 2026", 1)]),
    ("c02", "What is the minimum age for Class I?", [J("circ-kol-2026-004", "The minimum age for Class I is 6 years"), J("guide-admission-2026", "The minimum age for Class I is 6 years")]),
    ("c03", "What is the science cut-off at Bethune Collegiate School?", [J("circ-kol-2026-018", "| Bethune Collegiate School | College Street | 100 | 82% |")]),
    ("c04", "How many Class XI seats does Don Bosco School have?", [J("note-sch-359684982", "Class XI intake: 140 seats")]),
    ("c05", "Which board is Nava Nalanda affiliated to?", [J("note-sch-1469812433", "is a CBSE school")]),
    ("c06", "When is the EWS lottery in 2026?", [J("circ-kol-2026-012", "will be held on 16 March 2026")]),
    ("c07", "Why was Jessore Road closed?", [J("circ-kol-2026-021", "Because of flyover repair work")]),
    ("c08", "Which road should Auxilium Convent buses use in May?", [J("circ-kol-2026-021", "must use VIP Road")]),
    ("c09", "When does the new session start for Darjeeling hill schools?", [J("circ-djl-2026-005", "will begin on 6 April 2026"), J("circ-djl-2026-002", "The new session begins on 2 March 2026", 1)]),
    ("c10", "Which documents are needed for school admission?", [J("circ-kol-2026-007", "Birth certificate issued by the municipality")]),
    ("c11", "What percentage of seats can go to siblings?", [J("circ-kol-2026-007", "siblings of current students")]),
    ("c12", "What is the cut-off at C.R. Boys High School?", [J("note-sch-359329404", "Science cut-off 2026: 65%"), J("circ-kol-2026-018", "| Chittaranjan Boys High School | Ballygunge | 110 | 65% |")]),
    ("c13", "Where is Mount Hermon School?", [J("note-sch-348917732", "Locality: North Point"), J("town-darjeeling", "where St. Michael's School and Mt. Hermon School are located")]),
    ("c14", "What is the Class XI intake of Barisha Sashibhusan Janakalyan Vidyapith?", [J("note-sch-359503327", "Class XI intake: 160 seats")]),
    ("c15", "Which road does Dum Dum lie along?", [J("town-kolkata-north", "Dum Dum lies along Jessore Road")]),
    ("c16", "What is the hostel fee at St. Paul's School?", []),
    ("c17", "How many teachers work at Hare School?", []),
    ("c18", "What is the school bus fare from Behala?", []),
    ("c19", "When is the Class X board exam in 2026?", []),
    ("c20", "Which schools in Patna follow the CBSE board?", []),
    ("c21", "What is the minimum age for nursery admission?", []),
    ("c22", "Does Loreto Convent Darjeeling offer boarding?", []),
    ("c23", "How do I apply for a scholarship?", []),
    ("c24", "What is the pass mark in the Madhyamik exam?", []),
    ("c25", "Who is the principal of Delhi Public School?", []),
    ("c26", "When are the hill schools' admission tests?", [J("circ-djl-2026-005", "postponed to 21 March 2026"), J("circ-djl-2026-002", "will be held on 14 February 2026", 1)]),
    ("c27", "What is the maximum age for Class I?", [J("circ-kol-2026-004", "The maximum age for Class I is 8 years"), J("guide-admission-2026", "The maximum age for Class I is 8 years")]),
    ("c28", "What share of seats is reserved for economically weaker sections?", [J("circ-kol-2026-012", "25 per cent of entry-level seats are reserved"), J("guide-admission-2026", "25 per cent of entry-level seats are reserved")]),
    ("c29", "What is the science cut-off at Baranagar Ramakrishna Mission?", [J("circ-kol-2026-018", "| Baranagar Ramakrishna Mission Ashrama High School | Baranagar | 160 | 80% |"), J("note-sch-284535702", "Science cut-off 2026: 80%")]),
    ("c30", "Which board does Loretto Convent follow?", [J("note-sch-348890269", "is a CISCE school")]),
    ("c31", "When must the transfer certificate be submitted?", [J("circ-kol-2026-007", "within 30 days of admission")]),
    ("c32", "Which circular superseded DEO/KOL/2025/031?", [J("circ-kol-2026-014", "This circular supersedes circular DEO/KOL/2025/031")]),
    ("c33", "How many seats does Delhi Public School have?", [J("note-sch-5341865", "200 seats in Class XI")]),
    ("c34", "Who should primary pupils be admitted near?", [J("guide-geography", "within 1 km of their home")]),
    ("c35", "What is the canteen menu at Holy Cross School?", []),
    ("c36", "What sports does Turnbull Boys High School offer?", []),
    ("c37", "Is there a ragging policy for hostels?", []),
    ("c38", "What is the Class XI cut-off at Holy Cross School?", []),
    ("c39", "When does the Darjeeling Toy Train run?", []),
    ("c40", "How many seats does Kendriya Vidyalaya Salt Lake have?", []),
]
CAL_SPLIT = {cid: ("fit" if i < 25 else "test") for i, (cid, *_rest) in enumerate(
    # interleave answerable and unanswerable so both splits contain both kinds
    sorted(CALIBRATION, key=lambda c: (int(c[0][1:]) % 8, c[0])))}

DEV = [
    ("d01", "When do Class XI application forms open in Kolkata for 2026?", "Forms open on 25 May 2026 and close on 10 June 2026, as revised by circular DEO/KOL/2026/014.", ["25 May 2026"], ["circ-kol-2026-014"], True),
    ("d02", "What is the minimum age for admission to Class I?", "6 years as on 31 March 2026.", ["6 years"], ["circ-kol-2026-004", "guide-admission-2026"], True),
    ("d03", "What is the 2026 science cut-off at Hare School?", "85%.", ["85"], ["circ-kol-2026-018", "note-sch-360501161"], True),
    ("d04", "Which circulars apply to the board of St Xaviers Collegiate?", "It is a CISCE school, so DEO/KOL/2026/012 (EWS reservation and lottery) and DEO/KOL/2026/007 (documents) apply.", ["DEO/KOL/2026/012"], ["circ-kol-2026-012", "circ-kol-2026-007"], True),
    ("d05", "Where is Loretto Convent located?", "In Chowrasta, Darjeeling, on Hill Cart Road (OSM building 348890269).", ["Chowrasta"], ["note-sch-348890269", "dir-darjeeling"], True),
    ("d06", "Which schools are within 300 m of Jessore Road?", None, None, ["circ-kol-2026-021", "town-kolkata-north"], True),
    ("d07", "When will the Darjeeling hill schools hold their admission tests?", "On 21 March 2026; circular DEO/DJL/2026/005 postponed them from 14 February 2026.", ["21 March 2026"], ["circ-djl-2026-005"], True),
    ("d08", "How many Class XI seats does DPS Rajarhat have?", "200 seats.", ["200"], ["note-sch-5341865"], True),
    ("d09", "What are the annual fees at Don Bosco School?", "I cannot answer this from the available sources.", [], [], False),
    ("d10", "Who won the IPL in 2025?", "Out of scope: refused.", [], [], False),
]


def near_jessore():
    """Reference answer for d06, computed from the layers (same method as relation building)."""
    import geopandas as gpd
    from scripts.world import SCHOOLS
    schools = gpd.read_file(config.LAYERS_GPKG, layer="schools").to_crs(32646)
    road = gpd.read_file(config.LAYERS_GPKG, layer="roads").to_crs(32646)
    line = road[road.name == "Jessore Road"].geometry.iloc[0]
    hits = schools[schools.geometry.distance(line) <= 300]
    named = {s["name"] for s in SCHOOLS.values() if set(s["osm"]) & set(hits.osm_id)}
    named |= {n for n in hits.name.dropna()}
    return sorted(named)


def main():
    texts = {d["doc_id"]: d["text"] for d in load_documents()}

    def check(rows):
        for r in rows:
            for j in r["judgments"]:
                assert j["evidence"] in texts[j["doc_id"]], (r["id"], j)

    ret = [{"id": i, "split": s, "type": t, "query": q, "judgments": js} for i, s, t, q, js in RETRIEVAL]
    cal = [{"id": i, "split": CAL_SPLIT[i], "question": q, "answerable": bool(js), "judgments": js} for i, q, js in CALIBRATION]
    jessore = near_jessore()
    dev = []
    for i, q, ref, facts, docs, ok in DEV:
        if i == "d06":
            ref, facts = "Within 300 m of Jessore Road: " + ", ".join(jessore) + ".", jessore
        dev.append({"id": i, "question": q, "reference_answer": ref, "key_facts": facts, "gold_docs": docs,
                    "answerable": ok, "judgments": []})
    check(ret)
    check(cal)
    for name, rows in [("retrieval_judgments.jsonl", ret), ("calibration_questions.jsonl", cal), ("dev_questions.jsonl", dev)]:
        with open(config.EVAL_DIR / name, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"retrieval {len(ret)} (tune {sum(r['split'] == 'tune' for r in ret)}), calibration {len(cal)} "
          f"(fit {sum(r['split'] == 'fit' for r in cal)}, answerable {sum(r['answerable'] for r in cal)}), dev {len(dev)}")
    print("d06 reference:", jessore)


if __name__ == "__main__":
    main()
