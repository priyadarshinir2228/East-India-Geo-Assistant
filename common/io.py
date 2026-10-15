import json
from pathlib import Path


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_md_table(path, title, headers, rows, notes=""):
    """Write a results table as Markdown so it can be pasted into the PROJECT DOCUMENT."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    lines = [f"## {title}", "", "| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    if notes:
        lines += ["", notes]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
