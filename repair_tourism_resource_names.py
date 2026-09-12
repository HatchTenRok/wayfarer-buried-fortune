import json
from pathlib import Path

import geopandas as gpd


APP_ROOT = Path(__file__).resolve().parent
WAYFARER_ROOT = Path(r"C:\WayfarerData\wayfarer-data")
SOURCE_ROOT = WAYFARER_ROOT / "workspace" / "extracted" / "mlit" / "P19"
MUNICIPALITY_DIR = APP_ROOT / "data" / "by_municipality"
REPORT_PATH = APP_ROOT / "reports" / "tourism_resource_name_repair.json"


def coord_key(lon, lat):
    return f"{float(lon):.6f},{float(lat):.6f}"


def build_source_lookup():
    lookup = {}
    geometry_counts = {}
    for path in sorted(SOURCE_ROOT.glob("P19-12_*_GML/P19-12_*.shp")):
        data = gpd.read_file(path, encoding="cp932")
        for _, row in data.iterrows():
            geom = row.geometry
            geometry_counts[geom.geom_type] = geometry_counts.get(geom.geom_type, 0) + 1
            if geom.geom_type != "Point":
                continue
            name = str(row.get("P19_008") or "").strip()
            subtype = str(row.get("P19_007") or "").strip()
            resource_type = str(row.get("P19_005") or "").strip()
            resource_code = str(row.get("P19_006") or "").strip()
            if not name:
                continue
            lookup[coord_key(geom.x, geom.y)] = {
                "name": name,
                "address": " / ".join(value for value in [resource_type, subtype] if value),
                "resource_code": resource_code,
            }
    return lookup, geometry_counts


def main():
    lookup, geometry_counts = build_source_lookup()
    changed_files = 0
    changed_features = 0
    missing = 0
    examples = []

    for path in sorted(MUNICIPALITY_DIR.glob("*.geojson")):
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            if props.get("layer_id") != "tourism_resources":
                continue
            coords = (feature.get("geometry") or {}).get("coordinates")
            if not isinstance(coords, list) or len(coords) < 2:
                missing += 1
                continue
            source = lookup.get(coord_key(coords[0], coords[1]))
            if not source:
                missing += 1
                continue
            before = {"name": props.get("name"), "address": props.get("address")}
            props["name"] = source["name"]
            props["address"] = source["address"]
            props["resource_code"] = source["resource_code"]
            changed = True
            changed_features += 1
            if len(examples) < 20:
                examples.append(
                    {
                        "municipality_code": data.get("municipality_code"),
                        "city": data.get("city"),
                        "before": before,
                        "after": {
                            "name": props.get("name"),
                            "address": props.get("address"),
                            "resource_code": props.get("resource_code"),
                        },
                        "coordinates": coords[:2],
                    }
                )
        if changed:
            changed_files += 1
            path.write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
                newline="\n",
            )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "changed_files": changed_files,
                "changed_features": changed_features,
                "missing_source_matches": missing,
                "source_geometry_counts": geometry_counts,
                "examples": examples,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "changed_files": changed_files,
                "changed_features": changed_features,
                "missing_source_matches": missing,
                "source_geometry_counts": geometry_counts,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
