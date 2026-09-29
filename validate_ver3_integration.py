#!/usr/bin/env python3
"""Validate the generated Ver3 municipality data and UI contracts."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EXPECTED_CODES = {
    row["municipality_code"]
    for row in json.loads((DATA / "municipalities.json").read_text(encoding="utf-8"))
}
EXPECTED_LAYERS = {
    "historical_temples_shrines",
    "historical_sites_archaeology",
    "bakumatsu_villages",
    "edo_roads",
    "edo_post_stations",
    "civil_engineering_heritage",
}
EXPECTED_METRICS = {
    "dining",
    "parks",
    "public",
    "culture",
    "landscape",
    "temples_shrines",
    "historic_sites",
    "roads_posts",
    "villages",
    "civil",
}
ALLOWED_GEOMETRIES = {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}
FACILITY_LAYERS = {"public_facilities", "cultural_facilities"}
DISABILITY_PATTERN = re.compile(
    r"(?:障害|障がい|障碍)(?:者|児)|身体障害|知的障害|精神障害|視覚障害|聴覚障害|"
    r"視聴覚障|障害福祉|障がい福祉|盲人|ろうあ|聾唖|点字図書館|福祉作業所|"
    r"就労(?:移行|継続)支援|生活介護事業所",
    re.IGNORECASE,
)
NAME_NOISE = re.compile(r"[\s　・･「」『』（）()【】\[\]〈〉《》\"'’‘“”\-‐‑–—_]+")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def walk_coordinates(value):
    if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
        yield value[0], value[1]
        return
    if isinstance(value, list):
        for child in value:
            yield from walk_coordinates(child)


def normalized_name(value: object) -> str:
    return NAME_NOISE.sub("", unicodedata.normalize("NFKC", str(value or "")).lower())


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    layer_counts: Counter[str] = Counter()
    geometry_counts: Counter[str] = Counter()
    base_layer_counts: Counter[str] = Counter()
    base_feature_count = 0
    roadside_station_count = 0
    industrial_card_names = 0
    history_dir = DATA / "history_by_municipality"
    base_dir = DATA / "by_municipality"
    profile_dir = DATA / "profiles"
    history_codes = {path.stem for path in history_dir.glob("*.geojson")}
    profile_codes = {path.stem for path in profile_dir.glob("*.json")}
    if history_codes != EXPECTED_CODES:
        errors.append(f"history code mismatch: missing={len(EXPECTED_CODES-history_codes)} extra={len(history_codes-EXPECTED_CODES)}")
    if profile_codes != EXPECTED_CODES:
        errors.append(f"profile code mismatch: missing={len(EXPECTED_CODES-profile_codes)} extra={len(profile_codes-EXPECTED_CODES)}")

    largest_files: list[tuple[int, str, int]] = []
    for code in sorted(EXPECTED_CODES):
        history_path = history_dir / f"{code}.geojson"
        base_path = base_dir / f"{code}.geojson"
        profile_path = profile_dir / f"{code}.json"
        history = load(history_path)
        base = load(base_path)
        profile = load(profile_path)
        if history.get("municipality_code") != code:
            errors.append(f"{code}: history municipality_code mismatch")
        if profile.get("municipality_code") != code:
            errors.append(f"{code}: profile municipality_code mismatch")
        calculated_base_counts: Counter[str] = Counter()
        seen_facility_names: set[str] = set()
        for index, feature in enumerate(base.get("features", [])):
            props = feature.get("properties") or {}
            layer_id = props.get("layer_id", "unknown")
            name = str(props.get("name") or "")
            calculated_base_counts[layer_id] += 1
            base_layer_counts[layer_id] += 1
            base_feature_count += 1
            if DISABILITY_PATTERN.search(unicodedata.normalize("NFKC", name)):
                errors.append(f"{code}:{index}: disability facility remains")
            if props.get("source") == "国土数値情報 道の駅（P35-18）":
                roadside_station_count += 1
                if layer_id != "public_facilities":
                    errors.append(f"{code}:{index}: roadside station is not public_facilities")
            if layer_id in FACILITY_LAYERS and (feature.get("geometry") or {}).get("type") == "Point":
                key = normalized_name(name)
                if key and key in seen_facility_names:
                    errors.append(f"{code}:{index}: duplicate same-name public/cultural pin")
                if key:
                    seen_facility_names.add(key)
        if dict(sorted(calculated_base_counts.items())) != base.get("layer_counts", {}):
            errors.append(f"{code}: base layer_counts mismatch")
        if base.get("total_features") != len(base.get("features", [])):
            errors.append(f"{code}: base total_features mismatch")
        if history.get("type") != "FeatureCollection" or not isinstance(history.get("features"), list):
            errors.append(f"{code}: invalid FeatureCollection")
            continue
        calculated_counts: Counter[str] = Counter()
        for index, feature in enumerate(history["features"]):
            props = feature.get("properties") or {}
            geometry = feature.get("geometry") or {}
            layer_id = props.get("layer_id")
            geometry_type = geometry.get("type")
            if layer_id not in EXPECTED_LAYERS:
                errors.append(f"{code}:{index}: unexpected layer {layer_id!r}")
            if geometry_type not in ALLOWED_GEOMETRIES:
                errors.append(f"{code}:{index}: invalid geometry {geometry_type!r}")
            if not props.get("name") or not props.get("source"):
                errors.append(f"{code}:{index}: missing name/source")
            coordinate_count = 0
            for longitude, latitude in walk_coordinates(geometry.get("coordinates")):
                coordinate_count += 1
                if not (math.isfinite(longitude) and math.isfinite(latitude)):
                    errors.append(f"{code}:{index}: non-finite coordinate")
                    break
                if not (120 <= longitude <= 155 and 20 <= latitude <= 50):
                    errors.append(f"{code}:{index}: coordinate outside Japan bounds")
                    break
            if coordinate_count == 0:
                errors.append(f"{code}:{index}: empty coordinates")
            calculated_counts[layer_id] += 1
            layer_counts[layer_id] += 1
            geometry_counts[geometry_type] += 1
        if dict(sorted(calculated_counts.items())) != history.get("layer_counts", {}):
            errors.append(f"{code}: layer_counts mismatch")
        if history.get("total_features") != len(history["features"]):
            errors.append(f"{code}: total_features mismatch")
        largest_files.append((history_path.stat().st_size, history_path.name, len(history["features"])))

        groups = profile.get("radar_groups")
        if not isinstance(groups, list) or len(groups) != 2:
            errors.append(f"{code}: expected two radar groups")
            continue
        metrics = [metric for group in groups for metric in group.get("metrics", [])]
        if {metric.get("id") for metric in metrics} != EXPECTED_METRICS:
            errors.append(f"{code}: radar metric set mismatch")
        for metric in metrics:
            count = metric.get("count")
            rank = metric.get("rank")
            percentile = metric.get("percentile")
            if not isinstance(count, int) or count < 0:
                errors.append(f"{code}:{metric.get('id')}: invalid count")
            if count == 0 and rank is not None:
                errors.append(f"{code}:{metric.get('id')}: zero count must have null rank")
            if count > 0 and (not isinstance(rank, int) or not 1 <= rank <= len(EXPECTED_CODES)):
                errors.append(f"{code}:{metric.get('id')}: invalid rank")
            if not isinstance(percentile, (int, float)) or not 0 <= percentile <= 100:
                errors.append(f"{code}:{metric.get('id')}: invalid percentile")
        metric_by_id = {metric.get("id"): metric for metric in metrics}
        headline = profile.get("headline", "")
        dining = metric_by_id.get("dining", {})
        if "飲食店" in headline and not (
            isinstance(dining.get("rank"), int) and dining["rank"] <= 30
        ):
            errors.append(f"{code}: headline mentions dining below national top 30")
        if metric_by_id.get("civil", {}).get("count", 0) >= 1 and "土木遺産" not in headline:
            errors.append(f"{code}: headline omits civil heritage")
        if metric_by_id.get("roads_posts", {}).get("count", 0) >= 1 and "街道" not in headline:
            errors.append(f"{code}: headline omits road/post-station trace")
        if metric_by_id.get("villages", {}).get("count", 0) >= 5 and "村の境界" not in headline:
            errors.append(f"{code}: headline omits early-modern village trace")
        cards = profile.get("culture_cards") or {}
        if not profile.get("wiki_summary_title"):
            errors.append(f"{code}: missing wiki_summary_title")
        for key in ("notable_people", "tourism_landmarks", "food_culture", "mascots"):
            if not isinstance(cards.get(key), list):
                errors.append(f"{code}: culture card {key} is not a list")
        industrial_card_names += sum(
            str(item).endswith("（産業遺産）")
            for item in cards.get("tourism_landmarks", [])
        )

    app_js = (ROOT / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    for layer_id in EXPECTED_LAYERS:
        if layer_id not in app_js:
            errors.append(f"app.js missing layer {layer_id}")
    required_ids = {
        "restoreLayersButton",
        "resultHeadline",
        "wikiSummaryTitle",
        "storyText",
        "radarGrid",
        "metricDetails",
        "cultureCardGrid",
        "previousResultPage",
        "nextResultPage",
    }
    html_ids = set(re.findall(r'\bid="([^"]+)"', index_html))
    for element_id in required_ids - html_ids:
        errors.append(f"index.html missing #{element_id}")
    for obsolete_layer in ("historical_place_names", "industrial_heritage_reference"):
        if obsolete_layer in app_js:
            errors.append(f"app.js still exposes removed layer {obsolete_layer}")
    if 'new maplibregl.AttributionControl({ compact: false })' not in app_js:
        errors.append("app.js must keep map attribution expanded")
    if 'class="map-status-actions"' not in index_html:
        errors.append("index.html missing map status actions")
    if 'anchor: "bottom"' not in app_js:
        errors.append("app.js popup anchor must stay above the selected pin")
    if 'polygonOutlineLayerName(layerId)' not in app_js:
        errors.append("app.js missing early-modern village polygon outlines")
    if roadside_station_count != 1_145:
        errors.append(f"expected 1145 roadside stations, found {roadside_station_count}")
    cleanup_report = load(ROOT / "history_layer_cleanup_report.json")
    expected_industrial_names = cleanup_report.get("industrial_names_retained")
    if industrial_card_names != expected_industrial_names:
        errors.append(
            f"expected {expected_industrial_names} industrial landmark names, found {industrial_card_names}"
        )
    load(ROOT / "app_manifest.json")
    report = load(ROOT / "ver3_integration_report.json")
    retired_sources = {"historical_place_names.geojson", "industrial_heritage_meti.geojson"}
    unmatched = {
        source: values.get("unmatched", 0)
        for source, values in report.get("source_stats", {}).items()
        if values.get("unmatched") and source not in retired_sources
    }
    if unmatched:
        warnings.append(f"sources excluded because no valid current-municipality location was available: {unmatched}")

    summary = {
        "status": "PASS" if not errors else "FAIL",
        "municipalities": len(EXPECTED_CODES),
        "history_features": sum(layer_counts.values()),
        "base_features": base_feature_count,
        "base_layer_counts": dict(sorted(base_layer_counts.items())),
        "roadside_stations": roadside_station_count,
        "industrial_landmark_names": industrial_card_names,
        "layer_counts": dict(sorted(layer_counts.items())),
        "geometry_counts": dict(sorted(geometry_counts.items())),
        "largest_history_files": [
            {"file": name, "bytes": size, "features": count}
            for size, name, count in sorted(largest_files, reverse=True)[:10]
        ],
        "warnings": warnings,
        "errors": errors[:100],
    }
    (ROOT / "ver3_validation_report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
