"""Read GeoServer layers as GeoJSON over WFS, always as the read-only rag_geo user."""
import requests

from common import config

_cache = {}


def wfs_layer(layer):
    """Return the GeoJSON FeatureCollection of east_india:<layer> (cached per process)."""
    if layer not in _cache:
        r = requests.get(f"{config.GEOSERVER_URL}/{config.GS_WORKSPACE}/ows", timeout=60,
                         auth=(config.RAG_GEO_USER, config.RAG_GEO_PASSWORD),
                         params={"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                                 "typeNames": f"{config.GS_WORKSPACE}:{layer}", "outputFormat": "application/json",
                                 "srsName": "EPSG:4326"})
        r.raise_for_status()
        _cache[layer] = r.json()
    return _cache[layer]
