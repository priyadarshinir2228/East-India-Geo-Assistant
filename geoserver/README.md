# GeoServer

- `setup_geoserver.py` (as admin): workspace `east_india`, GeoPackage store from `/opt/east_india_data/east_india.gpkg`, layers `schools`, `roads`, `landuse`; user `rag_geo` with role `ROLE_RAG_GEO`; layer rules `east_india.*.r = ROLE_RAG_GEO,ADMIN` and `east_india.*.w = ADMIN`; catalogue mode CHALLENGE.
- `check_access.py`: anonymous WFS gets 401, `rag_geo` reads GeoJSON, a WFS-T insert by `rag_geo` gets 403.
