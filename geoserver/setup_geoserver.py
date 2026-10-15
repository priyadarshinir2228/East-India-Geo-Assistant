"""Task 1.5: publish workspace east_india (schools, roads, landuse) and lock it to a read-only user.

Runs once with the GeoServer admin account (from .env). Steps:
  1. workspace east_india + GeoPackage store pointing at data/geoserver/east_india.gpkg
  2. publish layers schools, roads, landuse
  3. role ROLE_RAG_GEO, user rag_geo with that role
  4. data rules: east_india.*.r -> ROLE_RAG_GEO,ADMIN (no anonymous read); writes stay admin-only
  5. catalog mode CHALLENGE so anonymous requests get HTTP 401 instead of a silent empty result
Run: python -m geoserver.setup_geoserver
"""
import requests

from common import config

WS = config.GS_WORKSPACE
GPKG_IN_CONTAINER = "/opt/east_india_data/east_india.gpkg"
REST = config.GEOSERVER_URL + "/rest"
AUTH = ("admin", config.GEOSERVER_ADMIN_PASSWORD)
J = {"Content-Type": "application/json"}


def call(method, path, ok=(200, 201), **kw):
    r = requests.request(method, REST + path, auth=AUTH, timeout=60, **kw)
    if r.status_code not in ok:
        raise SystemExit(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r


def exists(path):
    return requests.get(REST + path, auth=AUTH, timeout=30).status_code == 200


def main():
    if not exists(f"/workspaces/{WS}.json"):
        call("POST", "/workspaces", json={"workspace": {"name": WS}}, headers=J)
    if not exists(f"/workspaces/{WS}/datastores/east_india_gpkg.json"):
        call("POST", f"/workspaces/{WS}/datastores", headers=J, json={"dataStore": {
            "name": "east_india_gpkg",
            "connectionParameters": {"entry": [
                {"@key": "dbtype", "$": "geopkg"}, {"@key": "database", "$": GPKG_IN_CONTAINER},
                {"@key": "read_only", "$": "true"}]}}})
    for layer in ["schools", "roads", "landuse"]:
        if not exists(f"/workspaces/{WS}/datastores/east_india_gpkg/featuretypes/{layer}.json"):
            call("POST", f"/workspaces/{WS}/datastores/east_india_gpkg/featuretypes", headers=J,
                 json={"featureType": {"name": layer, "nativeName": layer, "srs": "EPSG:4326"}})
    # security: role, user, assignment
    if "ROLE_RAG_GEO" not in call("GET", "/security/roles.json").json().get("roles", []):
        call("POST", "/security/roles/role/ROLE_RAG_GEO")
    users = call("GET", "/security/usergroup/users.json").json()
    if not any(u["userName"] == config.RAG_GEO_USER for u in users.get("users", [])):
        call("POST", "/security/usergroup/users", headers=J, json={"user": {
            "userName": config.RAG_GEO_USER, "password": config.RAG_GEO_PASSWORD, "enabled": True}})
    call("POST", f"/security/roles/role/ROLE_RAG_GEO/user/{config.RAG_GEO_USER}", ok=(200, 201))
    rules = {f"{WS}.*.r": "ROLE_RAG_GEO,ADMIN", f"{WS}.*.w": "ADMIN"}
    current = call("GET", "/security/acl/layers.json").json()
    method = "PUT" if all(k in current for k in rules) else "POST"
    if method == "POST":
        rules = {k: v for k, v in rules.items() if k not in current}
    call(method, "/security/acl/layers", json=rules, headers=J)
    call("PUT", "/security/acl/catalog", headers=J, json={"mode": "CHALLENGE"})
    print(f"workspace {WS}: layers schools, roads, landuse; user {config.RAG_GEO_USER} read-only; catalog mode CHALLENGE")


if __name__ == "__main__":
    main()
