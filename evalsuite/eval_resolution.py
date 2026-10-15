"""Task 2.4: choose the school-linking threshold, then list merged variants and unlinked schools.

For each known name variant (with its document's locality as context) we run the real linker
at several thresholds and count: correct link, wrong link, no link. Names of schools that are
not in the layer (Sunrise Public School, Kendriya Vidyalaya Salt Lake) should get no link.
"""
from common import config
from common.io import read_jsonl, write_md_table
from ingest import resolve
from ingest.resolve import link_school, school_groups
from scripts.world import LOCALITIES, SCHOOLS, UNLINKED_SCHOOLS


def main():
    groups = school_groups()
    cases = [(v, set(s["osm"]), LOCALITIES[s["loc"]][1:3]) for s in SCHOOLS.values() for v in [s["name"]] + s["aliases"]]
    cases += [(s["name"], None, LOCALITIES[s["loc"]][1:3] if s["loc"] else None) for s in UNLINKED_SCHOOLS.values()]
    rows, best = [], None
    # before/after for the initials fix, at the chosen threshold
    fix_rows = []
    for flag in [False, True]:
        resolve.INITIALS_RULE = flag
        g, sc = link_school("K.K. Hindu Academy", groups, LOCALITIES["LOC-dum-dum"][1:3])
        fix_rows.append(f"| {'on' if flag else 'off'} | {g['name'] if g else 'not linked'} | {sc:.1f} |")
    for th in [70, 75, 80, 85, 88, 90, 95]:
        correct = wrong = missed = 0
        for name, osm, near in cases:
            g, _ = link_school(name, groups, near, threshold=th)
            if osm is None:
                correct, wrong = (correct + 1, wrong) if g is None else (correct, wrong + 1)
            elif g is None:
                missed += 1
            elif set(g["osm_ids"]) & osm:
                correct += 1
            else:
                wrong += 1
        rows.append([th, correct, wrong, missed, f"{correct / len(cases):.2f}"])
        if best is None or (correct, -wrong) > (best[1], -best[2]):
            best = rows[-1]
    unlinked = (config.WORK / "unlinked_schools.txt").read_text().split("\n") if (config.WORK / "unlinked_schools.txt").exists() else []
    ents = read_jsonl(config.WORK / "entities.jsonl") if (config.WORK / "entities.jsonl").exists() else []
    merged = [f"{e['canonical_name']}: {', '.join(e['aliases'])}" for e in ents
              if e["type"] == "School" and len(e["aliases"]) > 1 and not e["entity_id"].startswith("SCH-X")]
    write_md_table(config.RESULTS / "task2_resolution.md", "Task 2: school linking threshold",
                   ["Threshold", "Correct", "Wrong link", "No link (missed)", "Accuracy"], rows,
                   notes="**Fix: initials rule (before / after)**\n\n| Initials rule | 'K.K. Hindu Academy' links to | Score |\n|---|---|---|\n" +
                         "\n".join(fix_rows) + "\n\n" + f"{len(cases)} name variants ({len(UNLINKED_SCHOOLS)} of them should stay unlinked). "
                         f"Best threshold here: {best[0]}.\n\n**Merged variants (same GeoServer school)**\n\n" +
                         "\n".join(f"- {m}" for m in merged) + "\n\n**Schools that could not be linked to GeoServer**\n\n" +
                         "\n".join(f"- {u}" for u in unlinked if u))


if __name__ == "__main__":
    main()
