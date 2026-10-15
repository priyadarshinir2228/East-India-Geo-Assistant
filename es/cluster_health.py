"""Task 1.1: show cluster health (as rag_app, which has the monitor cluster privilege)."""
from common.es import app_client

h = app_client().cluster.health()
print({k: h[k] for k in ["cluster_name", "status", "number_of_nodes", "active_shards", "unassigned_shards"]})
if h["status"] == "yellow":
    print("Yellow: primaries are allocated but some replicas are not. On a single node a replica can never be "
          "placed on the same node as its primary, so any index with number_of_replicas >= 1 stays yellow. "
          "Our indices set number_of_replicas: 0, so the cluster is green unless another index has replicas.")
