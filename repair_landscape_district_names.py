import json
from collections import Counter
from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape


APP_ROOT = Path(__file__).resolve().parent
WAYFARER_ROOT = Path(r"C:\WayfarerData\wayfarer-data")
SOURCE_ROOT = WAYFARER_ROOT / "workspace" / "extracted" / "mlit" / "A35b"
MUNICIPALITY_DIR = APP_ROOT / "data" / "by_municipality"
REPORT_PATH = APP_ROOT / "reports" / "landscape_district_name_repair.json"


def geometry_key(geometry):
    if geometry is None or geometry.is_empty:
        return None
    minx, miny, maxx, maxy = geometry.bounds
    return (
        geometry.geom_type,
        round(minx, 8),
        round(miny, 8),
        round(maxx, 8),
        round(maxy, 8),
        round(geometry.centroid.x, 8),
        round(geometry.centroid.y, 8),
        round(geometry.area, 12),
    )


def row_text(row, field):
    value = row.get(field)
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def build_source_lookup():
    lookup = {}
    geometry_counts = {}
    for path in sorted(SOURCE_ROOT.glob("A35b-14_*_GML/A35*.shp")):
        data = gpd.read_file(path, encoding="cp932")
        source_kind = path.stem.split("-")[0]
        prefix = source_kind + "_"
        for _, row in data.iterrows():
            geom = row.geometry
            key = geometry_key(geom)
            if not key:
                continue
            geometry_counts[geom.geom_type] = geometry_counts.get(geom.geom_type, 0) + 1
            district_name = row_text(row, prefix + "005")
            detail_name = row_text(row, prefix + "006")
            if source_kind == "A35f":
                name = district_name
                address = ""
                subarea_name = detail_name
            else:
                name = district_name
                address = detail_name
                subarea_name = ""
            lookup[key] = {
                "name": name,
                "address": address,
                "subarea_name": subarea_name,
                "municipality_code_source": row_text(row, prefix + "004"),
                "source_kind": source_kind,
            }
    return lookup, geometry_counts


def main():
    lookup, geometry_counts = build_source_lookup()
    changed_files = 0
    changed_features = 0
    missing = 0
    examples = []
    display_name_counts = Counter()
    subarea_name_counts = Counter()

    for path in sorted(MUNICIPALITY_DIR.glob("*.geojson")):
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            if props.get("layer_id") != "landscape_districts":
                continue
            try:
                key = geometry_key(shape(feature.get("geometry")))
            except Exception:
                key = None
            source = lookup.get(key)
            if not source:
                missing += 1
                continue
            before = {"name": props.get("name"), "address": props.get("address")}
            props["name"] = source["name"]
            if source["address"]:
                props["address"] = source["address"]
            else:
                props.pop("address", None)
            if source["subarea_name"]:
                props["subarea_name"] = source["subarea_name"]
            else:
                props.pop("subarea_name", None)
            props["source_kind"] = source["source_kind"]
            display_name_counts[props.get("name", "")] += 1
            if props.get("subarea_name"):
                subarea_name_counts[props["subarea_name"]] += 1
            changed = True
            changed_features += 1
            if len(examples) < 25:
                examples.append(
                    {
                        "municipality_code": data.get("municipality_code"),
                        "city": data.get("city"),
                        "before": before,
                        "after": {
                            "name": props.get("name"),
                            "address": props.get("address"),
                            "subarea_name": props.get("subarea_name"),
                            "source_kind": props.get("source_kind"),
                        },
                        "geometry_type": (feature.get("geometry") or {}).get("type"),
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
                "unique_display_name_count": len(display_name_counts),
                "unique_subarea_name_count": len(subarea_name_counts),
                "display_names": [
                    {"name": name, "count": count}
                    for name, count in sorted(display_name_counts.items())
                    if name
                ],
                "subarea_names": [
                    {"name": name, "count": count}
                    for name, count in sorted(subarea_name_counts.items())
                    if name
                ],
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
