# Elasticsearch

- `setup_security.py` (as `elastic`): creates role `rag_app` (cluster `monitor`; `read`, `write`, `view_index_metadata` on the three indices) and an API key for it, written to `.env`.
- `setup_indices.py --dims 384 [--recreate]` (as `elastic`): creates `east_india_chunks`, `east_india_entities`, `east_india_relations` from `mappings/`, 1 shard, 0 replicas.
- `cluster_health.py` (as `rag_app`): cluster status and document counts.

Index names are lowercase because Elasticsearch rejects "East India_chunks".
