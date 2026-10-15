"""Build data/geoserver/east_india.gpkg with three layers: schools, roads, landuse.

schools: all 1,062 OSM school buildings from data/raw/schools.gpkg, plus synthetic
         board / seats / cutoff_marks for the schools in scripts/world.py.
roads, landuse: schematic synthetic layers (see PROJECT DOCUMENT, Disclosures).
Run: python -m scripts.make_layers
"""
import geopandas as gpd
from shapely.geometry import LineString, Point

from common import config
from scripts.world import BOARDS, LOCALITIES, ROADS, SCHOOLS


def main():
    src = gpd.read_file(config.DATA / "raw" / "schools.gpkg", layer="gis_osm_buildings_a_free_1")
    src = src[["osm_id", "name", "fclass", "type", "geometry"]].copy()
    attrs = {}
    for s in SCHOOLS.values():
        for osm in s["osm"]:
            attrs[osm] = (BOARDS[s["board"]]["short"], s["seats"], s["cutoff"])
    src["board"] = src["osm_id"].map(lambda o: attrs.get(o, (None,))[0])
    src["seats"] = src["osm_id"].map(lambda o: attrs[o][1] if o in attrs else None).astype("Int64")
    src["cutoff_marks"] = src["osm_id"].map(lambda o: attrs[o][2] if o in attrs else None).astype("Int64")
    src["synthetic_attrs"] = src["osm_id"].isin(attrs).astype(int)

    roads = gpd.GeoDataFrame(
        [{"road_id": rid, "name": name, "alt_names": "; ".join(alts), "fclass": "primary", "geometry": LineString(coords)}
         for rid, (name, alts, coords) in ROADS.items()], crs="EPSG:4326")

    # Landuse: a 1.2 km disc around each locality centre, buffered in metres (UTM 45N) then back to WGS84.
    pts = gpd.GeoDataFrame(
        [{"locality_id": lid, "name": name, "town": town, "fclass": "residential", "geometry": Point(lon, lat)}
         for lid, (name, lon, lat, town) in LOCALITIES.items()], crs="EPSG:4326")
    landuse = pts.to_crs(32645)
    landuse["geometry"] = landuse.buffer(1200)
    landuse = landuse.to_crs(4326)

    out = config.LAYERS_GPKG
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    src.to_file(out, layer="schools", driver="GPKG")
    roads.to_file(out, layer="roads", driver="GPKG")
    landuse.to_file(out, layer="landuse", driver="GPKG")
    print(f"wrote {out}: schools={len(src)} (with attrs={int(src.synthetic_attrs.sum())}), roads={len(roads)}, landuse={len(landuse)}")


if __name__ == "__main__":
    main()
