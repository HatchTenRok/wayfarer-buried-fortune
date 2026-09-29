#!/usr/bin/env python3
"""Build municipality-scoped history data and result profiles from the Ver3 pack.

The browser never reads the nationwide source files directly. This script spatially
joins the sources to the app's modern municipality boundaries, writes one small
GeoJSON and one profile JSON per municipality, and precomputes national ranks.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
import sys
import zipfile
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
BOUNDARY_DIR = DATA_DIR / "boundaries"
BASE_DATA_DIR = DATA_DIR / "by_municipality"
HISTORY_DATA_DIR = DATA_DIR / "history_by_municipality"
PROFILE_DIR = DATA_DIR / "profiles"
ATTRIBUTION_DIR = APP_DIR / "attribution"

GRID_SIZE = 0.25
TOTAL_MUNICIPALITIES = 1_896

HISTORY_LAYER_LABELS = {
    "historical_temples_shrines": "寺社仏閣",
    "historical_sites_archaeology": "史跡・遺跡",
    "bakumatsu_villages": "近世村のおおよその範囲",
    "edo_roads": "江戸期の街道",
    "edo_post_stations": "宿場",
    "civil_engineering_heritage": "土木遺産",
}

RADAR_GROUPS = [
    {
        "id": "town",
        "title": "街の基盤",
        "metrics": [
            ("dining", "飲食店", "飲食"),
            ("parks", "公園・遊具", "公園"),
            ("public", "公共施設", "公共"),
            ("culture", "文化施設", "文化"),
            ("landscape", "景観・樹木", "景観"),
        ],
    },
    {
        "id": "history",
        "title": "歴史資産",
        "metrics": [
            ("temples_shrines", "寺社仏閣", "寺社"),
            ("historic_sites", "史跡・遺跡", "史跡"),
            ("roads_posts", "街道・宿場", "街道"),
            ("villages", "近世村", "近世村"),
            ("civil", "土木遺産", "土木"),
        ],
    },
]

BASE_METRIC_LAYERS = {
    "dining": "cafe_restaurant",
    "parks": "parks_playgrounds",
    "public": "public_facilities",
    "culture": "cultural_facilities",
    "landscape": "landscape_important_buildings_trees",
}


def build_profile_headline(metrics: list[dict[str, Any]]) -> str:
    """Build a short, count-aware heading without overstating rare assets."""
    metric_by_id = {item.get("id"): item for item in metrics}
    roads = metric_by_id.get("roads_posts", {})
    villages = metric_by_id.get("villages", {})
    civil = metric_by_id.get("civil", {})
    dining = metric_by_id.get("dining", {})
    sentences: list[str] = []

    has_roads = int(roads.get("count") or 0) >= 1
    has_village_traces = int(villages.get("count") or 0) >= 5
    if has_roads and has_village_traces:
        sentences.append(
            "街道の街の雰囲気が感じられ、村の境界の痕跡も見つかるかもしれません。"
        )
    elif has_roads:
        sentences.append("街道の街の雰囲気が感じられる可能性があります。")
    elif has_village_traces:
        sentences.append("村の境界の痕跡があるかもしれません。")

    if int(civil.get("count") or 0) >= 1:
        sentences.append(
            "貴重な土木遺産もあります。" if sentences else "貴重な土木遺産があります。"
        )

    dining_rank = dining.get("rank")
    if int(dining.get("count") or 0) > 0 and isinstance(dining_rank, int) and dining_rank <= 30:
        sentences.append(
            "飲食店も全国上位30位以内です。"
            if sentences
            else "飲食店が全国上位30位以内に入る街です。"
        )

    if sentences:
        return "".join(sentences)

    excluded_ids = {"dining", "roads_posts", "villages", "civil"}
    strongest = sorted(
        [
            item
            for item in metrics
            if item.get("id") not in excluded_ids and int(item.get("count") or 0) > 0
        ],
        key=lambda item: (-float(item.get("percentile") or 0), -int(item.get("count") or 0), item.get("label", "")),
    )[:2]
    if strongest:
        labels = "や".join(item["label"] for item in strongest)
        return f"{labels}が、この街を歩く手がかりになりそうです。"
    return "件数だけでは見えない手がかりを、地図と街歩きから探したい地域です。"


def summary_item(value: object, limit: int = 28) -> str:
    text = re.split(r"[（(]", str(value or ""), maxsplit=1)[0].strip(" \t　「」『』")
    return text if len(text) <= limit else f"{text[:limit]}…"


def build_wiki_summary_title(cards: dict[str, list[str]], comment: str = "") -> str:
    people = [summary_item(item) for item in cards.get("notable_people", []) if summary_item(item)]
    landmarks = [summary_item(item) for item in cards.get("tourism_landmarks", []) if summary_item(item)]
    foods = [summary_item(item) for item in cards.get("food_culture", []) if summary_item(item)]
    mascots = [summary_item(item) for item in cards.get("mascots", []) if summary_item(item)]

    if landmarks and people:
        return f"「{landmarks[0]}」と{people[0]}ゆかりの物語をたどる街です。"
    if len(landmarks) >= 2:
        return f"「{landmarks[0]}」や「{landmarks[1]}」を手がかりに、土地の物語をたどれる街です。"
    if landmarks and foods:
        return f"「{landmarks[0]}」と{foods[0]}から、土地の風土を感じられる街です。"
    if landmarks:
        return f"「{landmarks[0]}」を手がかりに、土地の物語をたどれる街です。"
    if people:
        second = f"や{people[1]}" if len(people) >= 2 else ""
        return f"{people[0]}{second}など、ゆかりの人物の足跡をたどれる街です。"
    if foods:
        return f"{foods[0]}など、地域に伝わる食文化を楽しめる街です。"
    if mascots:
        return f"{mascots[0]}と出会える、地域色豊かな街です。"
    first_sentence = str(comment or "").split("。", 1)[0].strip()
    if first_sentence:
        return f"{first_sentence[:54]}{'…' if len(first_sentence) > 54 else ''}。"
    return "地図と街歩きから、土地に眠る物語を探したい街です。"


def compact_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def refresh_profile_headlines() -> dict[str, int]:
    updated = 0
    checked = 0
    for path in sorted(PROFILE_DIR.glob("*.json")):
        profile = read_json(path)
        metrics = [
            metric
            for group in profile.get("radar_groups", [])
            for metric in group.get("metrics", [])
        ]
        headline = build_profile_headline(metrics)
        wiki_summary_title = build_wiki_summary_title(
            profile.get("culture_cards") or {}, profile.get("display_comment_enriched", "")
        )
        checked += 1
        if (
            profile.get("headline") == headline
            and profile.get("wiki_summary_title") == wiki_summary_title
        ):
            continue
        profile["headline"] = headline
        profile["wiki_summary_title"] = wiki_summary_title
        compact_json(path, profile)
        updated += 1
    return {"checked": checked, "updated": updated}


def refresh_profile_statistics() -> dict[str, int]:
    profiles = {
        path.stem: read_json(path)
        for path in sorted(PROFILE_DIR.glob("*.json"))
    }
    metric_counts: dict[str, dict[str, int]] = {}
    for code, profile in profiles.items():
        base = read_json(BASE_DATA_DIR / f"{code}.geojson")
        base_counts = base.get("layer_counts") or {}
        current_metrics = {
            metric.get("id"): metric
            for group in profile.get("radar_groups", [])
            for metric in group.get("metrics", [])
        }
        metric_counts[code] = {
            metric_id: int(base_counts.get(layer_id, 0))
            for metric_id, layer_id in BASE_METRIC_LAYERS.items()
        }
        for metric_id in ("temples_shrines", "historic_sites", "roads_posts", "villages", "civil"):
            metric_counts[code][metric_id] = int(current_metrics.get(metric_id, {}).get("count", 0))

    metric_ids = [metric_id for group in RADAR_GROUPS for metric_id, _label, _short in group["metrics"]]
    distributions = {
        metric_id: [metric_counts[code][metric_id] for code in profiles]
        for metric_id in metric_ids
    }
    averages = {
        metric_id: sum(values) / len(values)
        for metric_id, values in distributions.items()
    }

    for code, profile in profiles.items():
        flat_metrics = []
        for group in profile.get("radar_groups", []):
            for metric in group.get("metrics", []):
                metric_id = metric["id"]
                value = metric_counts[code][metric_id]
                values = distributions[metric_id]
                metric["count"] = value
                metric["rank"] = None if value <= 0 else sum(candidate > value for candidate in values) + 1
                metric["percentile"] = (
                    0.0 if value <= 0 else round(100.0 * sum(candidate < value for candidate in values) / max(1, len(values) - 1), 1)
                )
                metric["national_average"] = round(averages[metric_id], 1)
                metric["municipality_total"] = len(values)
                flat_metrics.append(metric)
        profile["headline"] = build_profile_headline(flat_metrics)
        profile["wiki_summary_title"] = build_wiki_summary_title(
            profile.get("culture_cards") or {}, profile.get("display_comment_enriched", "")
        )
        compact_json(PROFILE_DIR / f"{code}.json", profile)
    return {"profiles": len(profiles), "metrics": len(metric_ids)}


def zip_member(names: list[str], suffix: str, size: int | None = None) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if size is not None:
        matches = [name for name in matches if ZIP_INFOS[name].file_size == size]
    if len(matches) != 1:
        raise RuntimeError(f"Could not uniquely find {suffix!r}: {matches}")
    return matches[0]


def load_zip_json(archive: zipfile.ZipFile, member: str) -> Any:
    return json.loads(archive.read(member).decode("utf-8-sig"))


def geometry_polygons(geometry: dict[str, Any] | None) -> list[list[list[list[float]]]]:
    if not geometry:
        return []
    if geometry.get("type") == "Polygon":
        return [geometry.get("coordinates", [])]
    if geometry.get("type") == "MultiPolygon":
        return geometry.get("coordinates", [])
    return []


def ring_bounds(ring: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in ring]
    ys = [point[1] for point in ring]
    return min(xs), min(ys), max(xs), max(ys)


def point_on_segment(
    x: float,
    y: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> bool:
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross) > 1e-10:
        return False
    return (
        min(x1, x2) - 1e-10 <= x <= max(x1, x2) + 1e-10
        and min(y1, y2) - 1e-10 <= y <= max(y1, y2) + 1e-10
    )


def point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    previous = len(ring) - 1
    for index, current_point in enumerate(ring):
        x1, y1 = ring[previous]
        x2, y2 = current_point
        if point_on_segment(x, y, x1, y1, x2, y2):
            return True
        if (y1 > y) != (y2 > y):
            crossing_x = ((x2 - x1) * (y - y1)) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
        previous = index
    return inside


def point_in_polygon(point: tuple[float, float], rings: list[list[list[float]]]) -> bool:
    if not rings or not point_in_ring(point, rings[0]):
        return False
    return not any(point_in_ring(point, hole) for hole in rings[1:])


def grid_key(x: float, y: float) -> tuple[int, int]:
    return math.floor(x / GRID_SIZE), math.floor(y / GRID_SIZE)


def iter_grid(bounds: Iterable[float]) -> Iterable[tuple[int, int]]:
    west, south, east, north = bounds
    min_x, min_y = grid_key(west, south)
    max_x, max_y = grid_key(east, north)
    for gx in range(min_x, max_x + 1):
        for gy in range(min_y, max_y + 1):
            yield gx, gy


def round_coordinates(value: Any, digits: int = 6) -> Any:
    if isinstance(value, list):
        return [round_coordinates(child, digits) for child in value]
    if isinstance(value, float):
        return round(value, digits)
    return value


def first_coordinate(geometry: dict[str, Any] | None) -> tuple[float, float] | None:
    coordinates = geometry.get("coordinates") if geometry else None
    while isinstance(coordinates, list) and coordinates:
        if len(coordinates) >= 2 and all(isinstance(v, (int, float)) for v in coordinates[:2]):
            return float(coordinates[0]), float(coordinates[1])
        coordinates = coordinates[0]
    return None


def split_items(value: str | None) -> list[str]:
    if not value:
        return []
    values = re.split(r"[｜|]", value)
    seen: set[str] = set()
    result: list[str] = []
    for item in values:
        cleaned = re.sub(r"\s+", " ", item).strip(" ・、")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def merge_unique_items(*groups: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for group in groups:
        for item in group:
            cleaned = re.sub(r"\s+", " ", str(item or "")).strip(" ・、")
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
    return result


def merge_landmark_items(*groups: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for group in groups:
        for item in group:
            cleaned = re.sub(r"\s+", " ", str(item or "")).strip(" ・、")
            key = cleaned.removesuffix("（産業遺産）").strip()
            if key and key not in seen:
                seen.add(key)
                result.append(cleaned)
    return result


def make_feature(
    layer_id: str,
    name: str,
    geometry: dict[str, Any],
    source: str,
    *,
    address: str = "",
    subarea_name: str = "",
    feature_key: str = "",
    source_url: str = "",
    accuracy_note: str = "",
    subtype: str = "",
) -> dict[str, Any]:
    properties = {
        "layer_id": layer_id,
        "name": name or HISTORY_LAYER_LABELS[layer_id],
        "address": address,
        "source": source,
    }
    optional = {
        "subarea_name": subarea_name,
        "feature_key": feature_key,
        "source_url": source_url,
        "accuracy_note": accuracy_note,
        "subtype": subtype,
    }
    properties.update({key: value for key, value in optional.items() if value})
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            **geometry,
            "coordinates": round_coordinates(geometry.get("coordinates")),
        },
    }


def iter_lines(geometry: dict[str, Any] | None) -> Iterable[list[list[float]]]:
    if not geometry:
        return
    geometry_type = geometry.get("type")
    if geometry_type == "LineString":
        yield geometry.get("coordinates", [])
    elif geometry_type == "MultiLineString":
        yield from geometry.get("coordinates", [])


def build() -> dict[str, Any]:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_ver3_integration.py PATH_TO_VER3_ZIP")
    zip_path = Path(sys.argv[1]).resolve()
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)

    municipalities = read_json(DATA_DIR / "municipalities.json")
    if len(municipalities) != TOTAL_MUNICIPALITIES:
        raise RuntimeError(f"Expected {TOTAL_MUNICIPALITIES} municipalities, got {len(municipalities)}")
    municipality_by_code = {row["municipality_code"]: row for row in municipalities}
    codes = sorted(municipality_by_code)

    boundary_index_rows = read_json(DATA_DIR / "boundary_index.json")
    bounds_by_code = {
        row["municipality_code"]: tuple(row["bounds"])
        for row in boundary_index_rows
        if row.get("municipality_code") in municipality_by_code
    }
    boundary_areas = {
        code: max(0.0, bounds[2] - bounds[0]) * max(0.0, bounds[3] - bounds[1])
        for code, bounds in bounds_by_code.items()
    }
    grid: dict[tuple[int, int], list[str]] = defaultdict(list)
    for code, bounds in bounds_by_code.items():
        for cell in iter_grid(bounds):
            grid[cell].append(code)
    for cell in grid:
        grid[cell].sort(key=lambda code: boundary_areas[code])

    polygons_by_code: dict[str, list[tuple[list[list[list[float]]], tuple[float, float, float, float]]]] = {}

    def municipality_polygons(code: str):
        cached = polygons_by_code.get(code)
        if cached is not None:
            return cached
        boundary_path = BOUNDARY_DIR / f"{code}.geojson"
        polygons = []
        if boundary_path.is_file():
            boundary = read_json(boundary_path)
            for feature in boundary.get("features", []):
                for rings in geometry_polygons(feature.get("geometry")):
                    if rings and rings[0]:
                        polygons.append((rings, ring_bounds(rings[0])))
        polygons_by_code[code] = polygons
        return polygons

    @lru_cache(maxsize=300_000)
    def locate_cached(x: float, y: float) -> str | None:
        for code in grid.get(grid_key(x, y), []):
            west, south, east, north = bounds_by_code[code]
            if not (west <= x <= east and south <= y <= north):
                continue
            for rings, bounds in municipality_polygons(code):
                p_west, p_south, p_east, p_north = bounds
                if p_west <= x <= p_east and p_south <= y <= p_north and point_in_polygon((x, y), rings):
                    return code
        return None

    def locate(point: tuple[float, float] | list[float] | None) -> str | None:
        if not point or len(point) < 2:
            return None
        try:
            x, y = round(float(point[0]), 7), round(float(point[1]), 7)
        except (TypeError, ValueError):
            return None
        if not (120 <= x <= 155 and 20 <= y <= 50):
            return None
        return locate_cached(x, y)

    label_lookup: list[tuple[str, str]] = sorted(
        (
            (re.sub(r"\s+", "", f"{row['pref']}{row['city']}"), row["municipality_code"])
            for row in municipalities
        ),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )
    city_codes: dict[str, list[str]] = defaultdict(list)
    for row in municipalities:
        city_codes[re.sub(r"\s+", "", row["city"])].append(row["municipality_code"])
    unique_city_lookup = sorted(
        ((city, values[0]) for city, values in city_codes.items() if len(values) == 1),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )

    def code_from_text(value: str | None) -> str | None:
        normalized = re.sub(r"\s+", "", value or "")
        exact = next((code for label, code in label_lookup if label and label in normalized), None)
        if exact:
            return exact
        return next((code for city, code in unique_city_lookup if city and city in normalized), None)

    def point_segment_distance(
        point: tuple[float, float], start: list[float], end: list[float]
    ) -> float:
        x, y = point
        x1, y1 = start
        x2, y2 = end
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(x - x1, y - y1)
        ratio = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(x - (x1 + ratio * dx), y - (y1 + ratio * dy))

    def nearest_municipality(point: tuple[float, float] | None, limit: float = 0.08) -> str | None:
        if not point:
            return None
        x, y = point
        best_code = None
        best_distance = limit
        for code, (west, south, east, north) in bounds_by_code.items():
            if x < west - limit or x > east + limit or y < south - limit or y > north + limit:
                continue
            for rings, _bounds in municipality_polygons(code):
                if not rings:
                    continue
                ring = rings[0]
                for start, end in zip(ring, ring[1:]):
                    distance = point_segment_distance(point, start, end)
                    if distance < best_distance:
                        best_distance = distance
                        best_code = code
        return best_code

    history_features: dict[str, list[dict[str, Any]]] = defaultdict(list)
    history_items: dict[str, dict[str, set[str]]] = {
        code: defaultdict(set) for code in codes
    }
    industrial_landmarks: dict[str, list[str]] = defaultdict(list)
    source_stats: dict[str, Counter] = defaultdict(Counter)

    def add(
        code: str | None,
        feature: dict[str, Any],
        metric_id: str | None,
        item_key: str,
        source_id: str,
    ) -> None:
        if not code or code not in municipality_by_code:
            source_stats[source_id]["unmatched"] += 1
            return
        history_features[code].append(feature)
        if metric_id:
            history_items[code][metric_id].add(item_key)
        source_stats[source_id]["assigned"] += 1

    with zipfile.ZipFile(zip_path) as archive:
        global ZIP_INFOS
        ZIP_INFOS = {info.filename: info for info in archive.infolist()}
        names = list(ZIP_INFOS)

        profile_csv_member = next(
            name
            for name in names
            if name.count("/") == 1
            and name.endswith(".csv")
            and ZIP_INFOS[name].file_size == 6_649_311
        )
        profile_text = archive.read(profile_csv_member).decode("utf-8-sig")
        enrichment_rows = {
            row["municipality_code"].zfill(5): row
            for row in csv.DictReader(io.StringIO(profile_text))
        }

        poi_sources = [
            ("01_temples.geojson", "historical_temples_shrines", "temples_shrines", "寺院"),
            ("02_shrines.geojson", "historical_temples_shrines", "temples_shrines", "神社"),
            ("03_abandoned_temples_shrines.geojson", "historical_temples_shrines", "temples_shrines", "廃寺・廃社"),
            ("04_castles.geojson", "historical_sites_archaeology", "historic_sites", "城郭"),
            ("05_castle_ruins.geojson", "historical_sites_archaeology", "historic_sites", "城跡"),
            ("06_kofun.geojson", "historical_sites_archaeology", "historic_sites", "古墳"),
            ("07_mounds.geojson", "historical_sites_archaeology", "historic_sites", "塚"),
            ("08_archaeological_sites.geojson", "historical_sites_archaeology", "historic_sites", "遺跡"),
            ("09_historic_sites.geojson", "historical_sites_archaeology", "historic_sites", "史跡"),
            ("99_other_poi.geojson", "historical_sites_archaeology", "historic_sites", "その他"),
        ]
        for suffix, layer_id, metric_id, subtype in poi_sources:
            payload = load_zip_json(archive, zip_member(names, suffix))
            for index, raw_feature in enumerate(payload.get("features", [])):
                props = raw_feature.get("properties", {})
                geometry = raw_feature.get("geometry")
                point = first_coordinate(geometry)
                code = locate(point)
                item_key = f"{suffix}:{props.get('id') or index}"
                feature = make_feature(
                    layer_id,
                    props.get("name", ""),
                    geometry,
                    props.get("source", "Geoshape 日本歴史地名大系"),
                    address=props.get("address", ""),
                    subarea_name=subtype,
                    feature_key=item_key,
                    subtype=subtype,
                )
                add(code, feature, metric_id, item_key, suffix)
            source_stats[suffix]["source"] = len(payload.get("features", []))

        village_point_member = next(name for name in names if name.endswith("01_Village_point_data_v2.csv"))
        village_point_text = archive.read(village_point_member).decode("cp932")
        village_points = {}
        for row in csv.DictReader(io.StringIO(village_point_text)):
            try:
                village_points[row["VID"]] = (float(row["Longitude"]), float(row["Latitude"]))
            except (KeyError, TypeError, ValueError):
                continue

        village_suffix = "bakumatsu_village_polygons_z7.geojson"
        payload = load_zip_json(archive, zip_member(names, village_suffix))
        for index, raw_feature in enumerate(payload.get("features", [])):
            props = raw_feature.get("properties", {})
            geometry = raw_feature.get("geometry")
            vid = str(props.get("vid") or props.get("aid") or index)
            village_point = village_points.get(vid) or first_coordinate(geometry)
            code = locate(village_point) or nearest_municipality(village_point)
            item_key = f"village:{vid}"
            feature = make_feature(
                "bakumatsu_villages",
                props.get("mura_name", "近世村"),
                geometry,
                props.get("source", "Geoshape 幕末期近世村領域データセット"),
                address=" ".join(filter(None, [props.get("kuni_name"), props.get("gun_name")])),
                subarea_name="近世村のおおよその範囲",
                feature_key=item_key,
                accuracy_note="2015年農業集落境界をもとに復元した概略範囲で、江戸時代の正確な村境ではありません",
            )
            add(code, feature, "villages", item_key, village_suffix)
        source_stats[village_suffix]["source"] = len(payload.get("features", []))

        road_suffix = "edo_roads_v4.geojson"
        road_payload = load_zip_json(archive, zip_member(names, road_suffix))
        road_names: dict[str, str] = {}
        for road_index, raw_feature in enumerate(road_payload.get("features", [])):
            props = raw_feature.get("properties", {})
            road_id = str(props.get("road_id") or f"road-{road_index}")
            road_name = props.get("name") or "江戸期の街道"
            road_names[road_id] = road_name
            road_codes: set[str] = set()
            for line in iter_lines(raw_feature.get("geometry")):
                current_code: str | None = None
                current_coordinates: list[list[float]] = []

                def flush_fragment() -> None:
                    nonlocal current_coordinates
                    if current_code and len(current_coordinates) >= 2:
                        fragment_key = f"road:{road_id}"
                        feature = make_feature(
                            "edo_roads",
                            road_name,
                            {"type": "LineString", "coordinates": current_coordinates},
                            props.get("source", "CODH 江戸主要街道データセット Version 4"),
                            address=" → ".join(filter(None, [props.get("start"), props.get("end")])),
                            subarea_name="江戸期の主要街道",
                            feature_key=fragment_key,
                        )
                        add(current_code, feature, "roads_posts", fragment_key, road_suffix)
                        road_codes.add(current_code)
                    current_coordinates = []

                for start, end in zip(line, line[1:]):
                    midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
                    segment_code = locate(midpoint)
                    if segment_code != current_code:
                        flush_fragment()
                        current_code = segment_code
                        current_coordinates = [start, end] if segment_code else []
                    elif segment_code:
                        if not current_coordinates:
                            current_coordinates = [start, end]
                        else:
                            current_coordinates.append(end)
                flush_fragment()
            source_stats[road_suffix]["source"] += 1
            if not road_codes:
                source_stats[road_suffix]["unmatched_roads"] += 1

        post_suffix = "edo_post_stations_v1.geojson"
        post_payload = load_zip_json(archive, zip_member(names, post_suffix))
        for index, raw_feature in enumerate(post_payload.get("features", [])):
            props = raw_feature.get("properties", {})
            geometry = raw_feature.get("geometry")
            point = first_coordinate(geometry)
            code = locate(point)
            post_id = str(props.get("id") or props.get("jk_id") or index)
            item_key = f"post:{post_id}"
            road_name = road_names.get(str(props.get("road_id", "")), "")
            feature = make_feature(
                "edo_post_stations",
                props.get("name", "宿場"),
                geometry,
                props.get("source", "CODH 江戸宿場データセット Version 1"),
                subarea_name=road_name,
                feature_key=item_key,
            )
            add(code, feature, "roads_posts", item_key, post_suffix)
        source_stats[post_suffix]["source"] = len(post_payload.get("features", []))

        industrial_member = next(
            name
            for name in names
            if name.endswith(".geojson") and ZIP_INFOS[name].file_size == 1_244_064
        )
        industrial_payload = load_zip_json(archive, industrial_member)
        for raw_feature in industrial_payload.get("features", []):
            props = raw_feature.get("properties", {})
            geometry = raw_feature.get("geometry")
            point = first_coordinate(geometry)
            code = locate(point)
            name = re.sub(r"\s+", " ", str(props.get("name") or "")).strip()
            if code and code in municipality_by_code and name:
                industrial_landmarks[code].append(f"{name}（産業遺産）")
                source_stats["industrial_heritage_meti.geojson"]["assigned"] += 1
            else:
                source_stats["industrial_heritage_meti.geojson"]["unmatched"] += 1
        source_stats["industrial_heritage_meti.geojson"]["source"] = len(
            industrial_payload.get("features", [])
        )

        civil_member = next(
            name
            for name in names
            if name.endswith(".geojson") and ZIP_INFOS[name].file_size == 870_776
        )
        civil_payload = load_zip_json(archive, civil_member)
        for index, raw_feature in enumerate(civil_payload.get("features", [])):
            props = raw_feature.get("properties", {})
            geometry = raw_feature.get("geometry")
            item_key = f"civil:{index}:{props.get('name', '')}"
            points: list[list[float]] = []
            if geometry and geometry.get("type") == "Point":
                points = [geometry.get("coordinates", [])]
            elif geometry and geometry.get("type") == "MultiPoint":
                points = geometry.get("coordinates", [])
            grouped_points: dict[str, list[list[float]]] = defaultdict(list)
            for point in points:
                code = locate(point)
                if code:
                    grouped_points[code].append(point)
            if not grouped_points:
                source_stats["civil_heritage_jsce_complete.geojson"]["unmatched"] += 1
                continue
            for code, assigned_points in grouped_points.items():
                assigned_geometry = {
                    "type": "Point" if len(assigned_points) == 1 else "MultiPoint",
                    "coordinates": assigned_points[0] if len(assigned_points) == 1 else assigned_points,
                }
                feature = make_feature(
                    "civil_engineering_heritage",
                    props.get("name", "土木遺産"),
                    assigned_geometry,
                    "土木学会 選奨土木遺産",
                    address=props.get("location_raw", ""),
                    subarea_name=props.get("description", ""),
                    feature_key=item_key,
                    source_url=props.get("detail_url", ""),
                    accuracy_note="公式地図の位置を優先して収録しています",
                )
                add(code, feature, "civil", item_key, "civil_heritage_jsce_complete.geojson")
        source_stats["civil_heritage_jsce_complete.geojson"]["source"] = len(
            civil_payload.get("features", [])
        )

    base_counts: dict[str, dict[str, int]] = {}
    metric_counts: dict[str, dict[str, int]] = {}
    for code in codes:
        base = read_json(BASE_DATA_DIR / f"{code}.geojson")
        counts = {key: int(value) for key, value in base.get("layer_counts", {}).items()}
        base_counts[code] = counts
        metric_counts[code] = {
            "dining": counts.get("cafe_restaurant", 0),
            "parks": counts.get("parks_playgrounds", 0),
            "public": counts.get("public_facilities", 0),
            "culture": counts.get("cultural_facilities", 0),
            "landscape": counts.get("landscape_important_buildings_trees", 0),
            "temples_shrines": len(history_items[code]["temples_shrines"]),
            "historic_sites": len(history_items[code]["historic_sites"]),
            "roads_posts": len(history_items[code]["roads_posts"]),
            "villages": len(history_items[code]["villages"]),
            "civil": len(history_items[code]["civil"]),
        }

    all_metric_ids = [
        metric_id
        for group in RADAR_GROUPS
        for metric_id, _label, _short_label in group["metrics"]
    ]
    distributions = {
        metric_id: [metric_counts[code][metric_id] for code in codes]
        for metric_id in all_metric_ids
    }
    averages = {
        metric_id: sum(values) / len(values)
        for metric_id, values in distributions.items()
    }

    def metric_result(metric_id: str, label: str, short_label: str, code: str) -> dict[str, Any]:
        value = metric_counts[code][metric_id]
        values = distributions[metric_id]
        greater = sum(candidate > value for candidate in values)
        lower = sum(candidate < value for candidate in values)
        percentile = 0.0 if value <= 0 else 100.0 * lower / max(1, len(values) - 1)
        return {
            "id": metric_id,
            "label": label,
            "short_label": short_label,
            "count": value,
            "rank": None if value <= 0 else greater + 1,
            "percentile": round(percentile, 1),
            "national_average": round(averages[metric_id], 1),
            "municipality_total": len(values),
        }

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for code in codes:
        municipality = municipality_by_code[code]
        features = sorted(
            history_features.get(code, []),
            key=lambda feature: (
                feature["properties"].get("layer_id", ""),
                feature["properties"].get("name", ""),
                feature["properties"].get("feature_key", ""),
            ),
        )
        layer_counts = Counter(
            feature["properties"].get("layer_id", "unknown") for feature in features
        )
        compact_json(
            HISTORY_DATA_DIR / f"{code}.geojson",
            {
                "type": "FeatureCollection",
                "municipality_code": code,
                "pref": municipality["pref"],
                "city": municipality["city"],
                "layer_counts": dict(sorted(layer_counts.items())),
                "total_features": len(features),
                "features": features,
            },
        )

        radar_groups = []
        flat_metrics = []
        for group in RADAR_GROUPS:
            metrics = [metric_result(*metric, code) for metric in group["metrics"]]
            flat_metrics.extend(metrics)
            radar_groups.append({"id": group["id"], "title": group["title"], "metrics": metrics})
        headline = build_profile_headline(flat_metrics)

        row = enrichment_rows.get(code, {})
        comment = row.get("display_comment_enriched") or row.get("display_comment") or ""
        culture_cards = {
            "notable_people": split_items(row.get("notable_people")),
            "tourism_landmarks": merge_landmark_items(
                split_items(row.get("tourism_landmarks")), industrial_landmarks.get(code, [])
            ),
            "food_culture": split_items(row.get("food_culture")),
            "mascots": split_items(row.get("ゆるキャラ名称")),
        }
        profile = {
            "municipality_code": code,
            "pref": municipality["pref"],
            "city": municipality["city"],
            "headline": headline,
            "wiki_summary_title": build_wiki_summary_title(culture_cards, comment),
            "display_comment_enriched": comment,
            "radar_groups": radar_groups,
            "culture_cards": culture_cards,
            "enrichment_meta": {
                "wikipedia_title": row.get("wikipedia_title", ""),
                "wikipedia_url": row.get("wikipedia_url", ""),
                "status": row.get("enrichment_status", ""),
                "mascot_status": row.get("判定", ""),
            },
            "data_notes": [
                "近世村は2015年農業集落境界をもとに復元した、おおよその範囲です。",
                "産業遺産は名称情報のみを観光・歴史名所へ収録し、地図上のピンは表示していません。",
            ],
        }
        compact_json(PROFILE_DIR / f"{code}.json", profile)

    ATTRIBUTION_DIR.mkdir(parents=True, exist_ok=True)
    (ATTRIBUTION_DIR / "ver3_history_sources.txt").write_text(
        "\n".join(
            [
                "Ver3 history data integration",
                "",
                "- Geoshape 日本歴史地名大系 施設・地点項目データセット: CC BY 4.0",
                "- Geoshape 幕末期近世村領域データセット: CC BY-SA 4.0",
                "- CODH 江戸主要街道データセット Version 4: CC BY 4.0",
                "- CODH 江戸宿場データセット Version 1: CC BY 4.0",
                "- 土木学会 選奨土木遺産（公式地図座標を優先）",
                "- 近代化産業遺産（名称情報のみを観光・歴史名所カードへ収録）",
                "",
                "近世村ポリゴンは2015年農業集落境界をもとにした概略範囲です。",
            ]
        ),
        encoding="utf-8",
    )

    report = {
        "source_zip": str(zip_path),
        "municipality_count": len(codes),
        "history_feature_count": sum(len(features) for features in history_features.values()),
        "history_files": len(list(HISTORY_DATA_DIR.glob("*.geojson"))),
        "profile_files": len(list(PROFILE_DIR.glob("*.json"))),
        "history_bytes": sum(path.stat().st_size for path in HISTORY_DATA_DIR.glob("*.geojson")),
        "profile_bytes": sum(path.stat().st_size for path in PROFILE_DIR.glob("*.json")),
        "source_stats": {key: dict(value) for key, value in sorted(source_stats.items())},
        "locator_cache": {
            "hits": locate_cached.cache_info().hits,
            "misses": locate_cached.cache_info().misses,
            "size": locate_cached.cache_info().currsize,
        },
    }
    compact_json(APP_DIR / "ver3_integration_report.json", report)
    return report


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, ensure_ascii=False, indent=2))
