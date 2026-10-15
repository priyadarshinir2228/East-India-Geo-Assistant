"""Create the three indices with explicit mappings (admin, once). Index creation is the only
step that needs more than rag_app; ingestion itself runs as rag_app.
Run: python -m es.setup_indices --dims 384 [--recreate]
"""
import argparse
import json

from common import config
from common.es import admin_client

MAP_DIR = config.ROOT / "es" / "mappings"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", type=int, default=384, help="embedding size of the chosen model")
    ap.add_argument("--recreate", action="store_true")
    a = ap.parse_args()
    es = admin_client()
    for name, file in [(config.CHUNKS_INDEX, "chunks.json"), (config.ENTITIES_INDEX, "entities.json"),
                       (config.RELATIONS_INDEX, "relations.json")]:
        body = json.loads((MAP_DIR / file).read_text().replace("__DIMS__", str(a.dims)))
        if es.indices.exists(index=name):
            if not a.recreate:
                print(f"{name}: exists (use --recreate to drop)")
                continue
            es.indices.delete(index=name)
        es.indices.create(index=name, settings=body["settings"], mappings=body["mappings"])
        print(f"{name}: created")


if __name__ == "__main__":
    main()
