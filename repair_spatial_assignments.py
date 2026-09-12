import argparse
import json
import re
from collections import Counter
from pathlib import Path

import shapefile
from shapely import make_valid
from shapely.geometry import GeometryCollection, MultiPoint, Point, mapping, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree


APP_ROOT = Path(__file__).resolve().parent
WAYFARER_ROOT = Path(r"C:\WayfarerData\wayfarer-data")
SOURCE_ROOT = WAYFARER_ROOT / "workspace" / "extracted" / "mlit"
MUNICIPALITY_DIR = APP_ROOT / "data" / "by_municipality"
BOUNDARY_DIR = APP_ROOT / "data" / "boundaries"
MUNICIPALITIES_PATH = APP_ROOT / "data" / "municipalities.json"
INDEX_PATH = APP_ROOT / "indexes" / "municipality_layer_counts.json"
REPORT_PATH = APP_ROOT / "reports" / "spatial_assignment_repair.json"
NAME_REPORT_PATH = APP_ROOT / "reports" / "scenic_name_repair.json"

LAYER_NAMES = {
    11: "自然公園地域",
    12: "自然公園特別地域",
    13: "自然公園特別保護地区",
    14: "自然保全地域",
    15: "原生自然環境保全地域",
    16: "自然保全特別地区",
}


def load_geometry(value):
    geometry = shape(value)
    return make_valid(geometry) if not geometry.is_valid else geometry


def polygonal_only(geometry):
    if geometry.is_empty:
        return geometry
    if geometry.geom_type in {"Polygon", "MultiPolygon"}:
        return geometry
    if isinstance(geometry, GeometryCollection):
        polygons = [
            part
            for part in geometry.geoms
            if part.geom_type in {"Polygon", "MultiPolygon"} and not part.is_empty
        ]
        return unary_union(polygons) if polygons else GeometryCollection()
    return GeometryCollection()


def load_scenic_sources():
    geometries = []
    metadata = []
    for dataset in ("A10", "A11"):
        dataset_root = SOURCE_ROOT / dataset
        for path in sorted(dataset_root.glob(f"{dataset}-15_*_GML/*.shp")):
            reader = shapefile.Reader(str(path), encoding="shift_jis")
            fields = [field[0] for field in reader.fields[1:]]
            for source_record in reader.iterShapeRecords():
                geometry = load_geometry(source_record.shape.__geo_interface__)
                if geometry.is_empty:
                    continue
                record = dict(zip(fields, source_record.record))
                layer_number = int(record.get("LAYER_NO") or 0)
                geometries.append(geometry)
                metadata.append(
                    {
                        "dataset": dataset,
                        "layer_number": layer_number,
                        "layer_name": LAYER_NAMES.get(layer_number, "景観・自然エリア"),
                        "object_name": str(record.get("OBJ_NAME") or "").strip(),
                    }
                )
    return geometries, metadata, STRtree(geometries)


def match_scenic_source(geometry, source_geometries, source_metadata, source_tree):
    if geometry.is_empty or geometry.area <= 0:
        return None
    best_score = None
    best_metadata = None
    for index in source_tree.query(geometry):
        source_geometry = source_geometries[index]
        try:
            intersection_area = geometry.intersection(source_geometry).area
        except Exception:
            continue
        if intersection_area <= 0:
            continue
        coverage = intersection_area / geometry.area
        area_similarity = -abs(source_geometry.area - geometry.area)
        score = (round(coverage, 9), area_similarity)
        if best_score is None or score > best_score:
            best_score = score
            best_metadata = source_metadata[index]
    return best_metadata


def repair_scenic_name(properties, metadata):
    current_name = str(properties.get("name") or "").strip()
    invalid_names = {"", "名称不明", "不明", "景観・自然エリア"}
    if current_name not in invalid_names and not re.fullmatch(r"\d+", current_name):
        return False

    if metadata:
        object_name = metadata["object_name"]
        layer_name = metadata["layer_name"]
        useful_object_name = object_name and not re.fullmatch(r"\d+", object_name)
        properties["name"] = object_name if useful_object_name else layer_name
        if useful_object_name and layer_name != object_name:
            properties["subarea_name"] = layer_name
        else:
            properties.pop("subarea_name", None)
        properties["resource_class"] = layer_name
        properties["source_dataset_code"] = metadata["dataset"]
    else:
        properties["name"] = "景観・自然エリア"
    return True


def write_compact_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--names-only",
        action="store_true",
        help="Repair scenic-area display names without changing any geometry.",
    )
    args = parser.parse_args()

    source_geometries, source_metadata, source_tree = load_scenic_sources()
    municipalities = json.loads(MUNICIPALITIES_PATH.read_text(encoding="utf-8"))
    municipality_lookup = {item["municipality_code"]: item for item in municipalities}
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    totals_by_layer = Counter()
    removed_by_layer = Counter()
    report = {
        "mode": "names_only" if args.names_only else "spatial_and_names",
        "files_checked": 0,
        "files_changed": 0,
        "points_removed_outside": 0,
        "multipoints_removed_outside": 0,
        "polygons_removed_outside": 0,
        "polygons_clipped_to_boundary": 0,
        "scenic_names_repaired": 0,
        "scenic_source_unmatched": 0,
        "source_geometries": len(source_geometries),
        "examples": [],
    }

    for data_path in sorted(MUNICIPALITY_DIR.glob("*.geojson")):
        code = data_path.stem
        boundary_path = BOUNDARY_DIR / f"{code}.geojson"
        if not boundary_path.exists():
            continue

        data = json.loads(data_path.read_text(encoding="utf-8"))
        boundary_data = json.loads(boundary_path.read_text(encoding="utf-8"))
        boundary = unary_union(
            [load_geometry(feature["geometry"]) for feature in boundary_data.get("features", [])]
        )
        if boundary.is_empty:
            continue

        report["files_checked"] += 1
        changed = False
        kept_features = []
        for feature in data.get("features", []):
            properties = feature.get("properties") or {}
            layer_id = properties.get("layer_id") or "unknown"
            geometry_data = feature.get("geometry") or {}
            geometry_type = geometry_data.get("type")

            if args.names_only:
                if (
                    layer_id == "scenic_nature_areas"
                    and geometry_type in {"Polygon", "MultiPolygon"}
                ):
                    geometry = load_geometry(geometry_data)
                    metadata = match_scenic_source(
                        geometry, source_geometries, source_metadata, source_tree
                    )
                    if repair_scenic_name(properties, metadata):
                        report["scenic_names_repaired"] += 1
                        if metadata is None:
                            report["scenic_source_unmatched"] += 1
                        changed = True
                kept_features.append(feature)
                continue

            if geometry_type == "Point":
                point = Point(geometry_data.get("coordinates", []))
                if not boundary.covers(point):
                    report["points_removed_outside"] += 1
                    removed_by_layer[layer_id] += 1
                    changed = True
                    if len(report["examples"]) < 40:
                        report["examples"].append(
                            {"code": code, "action": "removed_point", "name": properties.get("name")}
                        )
                    continue

            elif geometry_type == "MultiPoint":
                points = [Point(coordinate) for coordinate in geometry_data.get("coordinates", [])]
                inside = [point for point in points if boundary.covers(point)]
                removed = len(points) - len(inside)
                if removed:
                    report["multipoints_removed_outside"] += removed
                    changed = True
                if not inside:
                    removed_by_layer[layer_id] += 1
                    continue
                if removed:
                    feature["geometry"] = mapping(MultiPoint(inside))

            elif geometry_type in {"Polygon", "MultiPolygon"}:
                geometry = load_geometry(geometry_data)
                if layer_id == "scenic_nature_areas":
                    metadata = match_scenic_source(
                        geometry, source_geometries, source_metadata, source_tree
                    )
                    if repair_scenic_name(properties, metadata):
                        report["scenic_names_repaired"] += 1
                        if metadata is None:
                            report["scenic_source_unmatched"] += 1
                        changed = True

                if not boundary.covers(geometry):
                    clipped = polygonal_only(geometry.intersection(boundary))
                    if clipped.is_empty:
                        report["polygons_removed_outside"] += 1
                        removed_by_layer[layer_id] += 1
                        changed = True
                        continue
                    feature["geometry"] = mapping(clipped)
                    report["polygons_clipped_to_boundary"] += 1
                    changed = True

            kept_features.append(feature)

        layer_counts = Counter(
            (feature.get("properties") or {}).get("layer_id") or "unknown"
            for feature in kept_features
        )
        data["features"] = kept_features
        data["layer_counts"] = dict(layer_counts)
        data["total_features"] = len(kept_features)
        totals_by_layer.update(layer_counts)

        if code in municipality_lookup:
            municipality_lookup[code]["feature_count"] = len(kept_features)
        index["by_municipality"][code] = {
            "municipality_code": code,
            "layers": dict(layer_counts),
            "total": len(kept_features),
        }

        if changed:
            write_compact_json(data_path, data)
            report["files_changed"] += 1

    index["layer_totals"] = dict(totals_by_layer)
    write_compact_json(MUNICIPALITIES_PATH, municipalities)
    write_compact_json(INDEX_PATH, index)
    report["removed_by_layer"] = dict(removed_by_layer)
    report_path = NAME_REPORT_PATH if args.names_only else REPORT_PATH
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
