"""Task 1.5 evidence: anonymous WFS is refused; rag_geo can read GeoJSON; rag_geo cannot write."""
import requests

from common import config

WFS = f"{config.GEOSERVER_URL}/{config.GS_WORKSPACE}/ows"
P = {"service": "WFS", "version": "2.0.0", "request": "GetFeature",
     "typeNames": f"{config.GS_WORKSPACE}:schools", "outputFormat": "application/json", "count": 3}

anon = requests.get(WFS, params=P, timeout=30)
print("anonymous GetFeature  ->", anon.status_code, anon.headers.get("WWW-Authenticate", ""))
ok = requests.get(WFS, params=P, auth=(config.RAG_GEO_USER, config.RAG_GEO_PASSWORD), timeout=30)
fc = ok.json()
print("rag_geo GetFeature    ->", ok.status_code, f"{fc.get('numberMatched')} features, first: "
      f"{fc['features'][0]['properties'].get('name')} {fc['features'][0]['properties'].get('osm_id')}")
tx = ('<wfs:Transaction service="WFS" version="2.0.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" '
      'xmlns:fes="http://www.opengis.net/fes/2.0"><wfs:Delete typeName="east_india:schools">'
      '<fes:Filter><fes:ResourceId rid="schools.1"/></fes:Filter></wfs:Delete></wfs:Transaction>')
w = requests.post(WFS, data=tx, headers={"Content-Type": "text/xml"},
                  auth=(config.RAG_GEO_USER, config.RAG_GEO_PASSWORD), timeout=30)
print("rag_geo Transaction   ->", w.status_code, w.text[:160].replace("\n", " "))
