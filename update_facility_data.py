"""Clean facility pins and integrate MLIT roadside-station data.

Dry-run is the default. Use --apply after inspecting the JSON report.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from build_ver3_integration import geometry_polygons, point_in_polygon


TARGET_LAYERS = {"public_facilities", "cultural_facilities"}
ROADSIDE_SOURCE = "国土数値情報 道の駅（P35-18）"
DISABILITY_PATTERN = re.compile(
    r"(?:障害|障がい|障碍)(?:者|児)|身体障害|知的障害|精神障害|"
    r"視覚障害|聴覚障害|視聴覚障|障害福祉|障がい福祉|"
    r"盲人|ろうあ|聾唖|点字図書館|福祉作業所|"
    r"就労(?:移行|継続)支援|生活介護事業所",
    re.IGNORECASE,
)
NAME_NOISE = re.compile(r"[\s　・･「」『』（）()【】\[\]〈〉《》\"'’‘“”\-‐‑–—_]+")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return NAME_NOISE.sub("", text)


def point_coordinates(feature: dict) -> list[float] | None:
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    if geometry.get("type") != "Point" or not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    try:
        return [float(coordinates[0]), float(coordinates[1])]
    except (TypeError, ValueError):
        return None


def consolidate_same_name_pins(features: list[dict], municipality_code: str):
    groups: dict[str, list[tuple[int, dict, list[float]]]] = defaultdict(list)
    for index, feature in enumerate(features):
        props = feature.get("properties") or {}
        if props.get("layer_id") not in TARGET_LAYERS:
            continue
        coordinates = point_coordinates(feature)
        key = normalize_name(props.get("name"))
        if coordinates and key:
            groups[key].append((index, feature, coordinates))

    replacements: dict[int, dict] = {}
    skipped: set[int] = set()
    samples = []
    removed_by_layer = Counter()
    duplicate_groups = 0

    for items in groups.values():
        if len(items) <= 1:
            continue
        duplicate_groups += 1
        first_index = min(item[0] for item in items)
        official = [item for item in items if (item[1].get("properties") or {}).get("source") == ROADSIDE_SOURCE]
        public = [item for item in items if (item[1].get("properties") or {}).get("layer_id") == "public_facilities"]
        preferred = (official or public or items)[0][1]
        replacement = copy.deepcopy(preferred)
        chosen_layer = (
            "public_facilities"
            if official
            else (preferred.get("properties") or {}).get("layer_id", "public_facilities")
        )
        centroid = [
            round(sum(item[2][axis] for item in items) / len(items), 7)
            for axis in (0, 1)
        ]
        replacement.setdefault("properties", {})["layer_id"] = chosen_layer
        replacement["geometry"] = {"type": "Point", "coordinates": centroid}
        replacements[first_index] = replacement
        for index, feature, _coordinates in items:
            if index == first_index:
                continue
            skipped.add(index)
            removed_by_layer[(feature.get("properties") or {}).get("layer_id", "unknown")] += 1
        if len(samples) < 40:
            samples.append(
                {
                    "municipality_code": municipality_code,
                    "name": replacement.get("properties", {}).get("name", ""),
                    "merged": len(items),
                    "centroid": centroid,
                    "coordinates": [item[2] for item in items],
                }
            )

    consolidated = []
    for index, feature in enumerate(features):
        if index in skipped:
            continue
        consolidated.append(replacements.get(index, feature))
    return consolidated, duplicate_groups, removed_by_layer, samples


def point_in_boundary(point: tuple[float, float], boundary: dict) -> bool:
    for feature in boundary.get("features", []):
        for rings in geometry_polygons(feature.get("geometry")):
            if point_in_polygon(point, rings):
                return True
    return False


def locate_missing_code(
    coordinates: list[float], boundary_index: list[dict], boundary_dir: Path
) -> str | None:
    longitude, latitude = coordinates
    candidates = []
    for row in boundary_index:
        west, south, east, north = row.get("bounds", [0, 0, 0, 0])
        if west <= longitude <= east and south <= latitude <= north:
            area = max(0.0, east - west) * max(0.0, north - south)
            candidates.append((area, row.get("municipality_code")))
    for _area, code in sorted(candidates):
        path = boundary_dir / f"{code}.geojson"
        if path.is_file() and point_in_boundary((longitude, latitude), load_json(path)):
            return code
    return None


def load_roadside_stations(
    archive_path: Path,
    municipality_by_code: dict[str, dict],
    boundary_index: list[dict],
    boundary_dir: Path,
):
    with zipfile.ZipFile(archive_path) as archive:
        member = next(name for name in archive.namelist() if name.endswith("_Roadside_Station.geojson"))
        source = json.loads(archive.read(member).decode("utf-8-sig"))

    by_code: dict[str, list[dict]] = defaultdict(list)
    unmatched = []
    reassigned = []
    for feature in source.get("features", []):
        props = feature.get("properties") or {}
        coordinates = point_coordinates(feature)
        source_code = str(props.get("P35_005") or "").zfill(5)
        code = source_code if source_code in municipality_by_code else None
        if not code and coordinates:
            code = locate_missing_code(coordinates, boundary_index, boundary_dir)
            if code:
                reassigned.append({"source_code": source_code, "assigned_code": code})
        if not code or not coordinates:
            unmatched.append({"source_code": source_code, "name": props.get("P35_006", "")})
            continue
        raw_name = str(props.get("P35_006") or "名称不明").strip()
        name = raw_name if raw_name.startswith("道の駅") else f"道の駅 {raw_name}"
        municipality = municipality_by_code[code]
        by_code[code].append(
            {
                "type": "Feature",
                "properties": {
                    "layer_id": "public_facilities",
                    "name": name,
                    "address": f"{municipality.get('pref', '')}{municipality.get('city', '')}",
                    "source": ROADSIDE_SOURCE,
                    "source_url": props.get("P35_007") or "",
                },
                "geometry": {"type": "Point", "coordinates": coordinates},
            }
        )
    return by_code, len(source.get("features", [])), unmatched, reassigned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("roadside_zip", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    base_dir = root / "data" / "by_municipality"
    boundary_dir = root / "data" / "boundaries"
    municipality_path = root / "data" / "municipalities.json"
    index_path = root / "indexes" / "municipality_layer_counts.json"
    municipalities = load_json(municipality_path)
    municipality_by_code = {item["municipality_code"]: item for item in municipalities}
    boundary_index = load_json(root / "data" / "boundary_index.json")
    roadside_by_code, roadside_source_count, roadside_unmatched, reassigned = load_roadside_stations(
        args.roadside_zip.resolve(), municipality_by_code, boundary_index, boundary_dir
    )

    total_before = 0
    total_after = 0
    removed_disability = Counter()
    disability_samples = []
    duplicate_removed = Counter()
    duplicate_groups = 0
    duplicate_samples = []
    layer_totals = Counter()
    municipality_counts = {}

    for path in sorted(base_dir.glob("*.geojson")):
        code = path.stem
        payload = load_json(path)
        original = payload.get("features", [])
        total_before += len(original)
        kept = []
        for feature in original:
            props = feature.get("properties") or {}
            name = unicodedata.normalize("NFKC", str(props.get("name") or ""))
            if DISABILITY_PATTERN.search(name):
                layer = props.get("layer_id", "unknown")
                removed_disability[layer] += 1
                if len(disability_samples) < 60:
                    disability_samples.append(
                        {"municipality_code": code, "layer_id": layer, "name": name}
                    )
                continue
            kept.append(feature)

        kept.extend(roadside_by_code.get(code, []))
        consolidated, groups, removed_layers, samples = consolidate_same_name_pins(kept, code)
        duplicate_groups += groups
        duplicate_removed.update(removed_layers)
        duplicate_samples.extend(samples[: max(0, 40 - len(duplicate_samples))])
        counts = Counter(
            (feature.get("properties") or {}).get("layer_id", "unknown")
            for feature in consolidated
        )
        payload["features"] = consolidated
        payload["layer_counts"] = dict(sorted(counts.items()))
        payload["total_features"] = len(consolidated)
        total_after += len(consolidated)
        layer_totals.update(counts)
        municipality_counts[code] = {
            "municipality_code": code,
            "layers": payload["layer_counts"],
            "total": payload["total_features"],
        }
        if args.apply:
            write_json(path, payload)

    if args.apply:
        for municipality in municipalities:
            municipality["feature_count"] = municipality_counts[municipality["municipality_code"]]["total"]
        write_json(municipality_path, municipalities)
        current_index = load_json(index_path)
        current_index["generated_at"] = datetime.now(timezone.utc).isoformat()
        current_index["by_municipality"] = municipality_counts
        current_index["layer_totals"] = dict(sorted(layer_totals.items()))
        write_json(index_path, current_index)

    report = {
        "mode": "apply" if args.apply else "dry-run",
        "base_features_before": total_before,
        "base_features_after": total_after,
        "roadside_source_features": roadside_source_count,
        "roadside_assigned": sum(len(items) for items in roadside_by_code.values()),
        "roadside_unmatched": roadside_unmatched,
        "roadside_parent_code_reassignments": reassigned,
        "disability_facilities_removed": sum(removed_disability.values()),
        "disability_removed_by_layer": dict(sorted(removed_disability.items())),
        "disability_samples": disability_samples,
        "duplicate_name_groups": duplicate_groups,
        "duplicate_pins_removed": sum(duplicate_removed.values()),
        "duplicate_removed_by_layer": dict(sorted(duplicate_removed.items())),
        "duplicate_samples": duplicate_samples,
        "layer_totals_after": dict(sorted(layer_totals.items())),
    }
    report_path = args.report or root / "facility_cleanup_and_road_station_report.json"
    write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
