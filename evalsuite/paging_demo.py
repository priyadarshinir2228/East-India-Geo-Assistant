"""Task 3.7: fetch page 2 (results 11-20) with a point-in-time and search_after."""
from common import config
from common.es import app_client

es = app_client()
query = {"match": {"text": "school"}}
pit = es.open_point_in_time(index=config.CHUNKS_INDEX, keep_alive="1m")["id"]
sort = [{"_score": "desc"}, {"chunk_id": "asc"}]  # chunk_id = unique tiebreaker so the order is total
page1 = es.search(query=query, size=10, pit={"id": pit, "keep_alive": "1m"}, sort=sort, source=["chunk_id"])
after = page1["hits"]["hits"][-1]["sort"]
page2 = es.search(query=query, size=10, pit={"id": page1["pit_id"], "keep_alive": "1m"}, sort=sort,
                  search_after=after, source=["chunk_id"])
print("page 1:", [h["_source"]["chunk_id"] for h in page1["hits"]["hits"]])
print("search_after =", after)
print("page 2:", [h["_source"]["chunk_id"] for h in page2["hits"]["hits"]])
es.close_point_in_time(id=page2["pit_id"])
print("\nWhy: from+size makes every shard collect and sort from+size hits, then throws away `from` of them, so cost grows "
      "with the page number (and from+size is capped at 10,000). search_after only asks for the 10 hits that sort after the "
      "last one seen, so each page costs the same; the point-in-time freezes the index view so pages stay consistent while "
      "documents are being added.")
