import json
from collections import Counter
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent
MUNICIPALITY_DIR = APP_ROOT / "data" / "by_municipality"
MUNICIPALITIES_PATH = APP_ROOT / "data" / "municipalities.json"
COUNTS_PATH = APP_ROOT / "indexes" / "municipality_layer_counts.json"
REPORT_PATH = APP_ROOT / "reports" / "known_coordinate_outliers_removed.json"

# The source rows say Fukuchiyama, but these coordinates land far outside the
# Fukuchiyama area around southern Kyoto/Nara. Keep this list explicit so wide
# merged municipalities and island municipalities are not accidentally trimmed.
KNOWN_OUTLIER_RULES = {
    "26201": {
        "reason": "福知山市の飲食店データに、住所と大きく離れた座標が混在していたため除外",
        "layers": {"cafe_restaurant"},
        "coordinate_boxes": [
            # lon_min, lat_min, lon_max, lat_max
            (135.70, 34.78, 135.91, 35.08),
        ],
    },
}


def feature_anchor(feature):
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    if geometry.get("type") == "Point" and is_lnglat(coordinates):
        return coordinates
    return None


def is_lnglat(value):
    return (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    )


def in_box(coord, box):
    lon, lat = coord[:2]
    lon_min, lat_min, lon_max, lat_max = box
    return lon_min <= lon <= lon_max and lat_min <= lat <= lat_max


def refresh_counts(data):
    counts = Counter()
    for feature in data.get("features", []):
        layer_id = (feature.get("properties") or {}).get("layer_id")
        if layer_id:
            counts[layer_id] += 1
    data["layer_counts"] = dict(sorted(counts.items()))
    data["total_features"] = sum(counts.values())


def update_indexes(code, data):
    if MUNICIPALITIES_PATH.exists():
        municipalities = json.loads(MUNICIPALITIES_PATH.read_text(encoding="utf-8"))
        for item in municipalities:
            if str(item.get("municipality_code")) == code:
                item["feature_count"] = data["total_features"]
                item["layer_counts"] = data["layer_counts"]
                break
        MUNICIPALITIES_PATH.write_text(
            json.dumps(municipalities, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
            newline="\n",
        )

    if COUNTS_PATH.exists():
        counts_index = json.loads(COUNTS_PATH.read_text(encoding="utf-8"))
        if code in counts_index:
            counts_index[code]["total_features"] = data["total_features"]
            counts_index[code]["layer_counts"] = data["layer_counts"]
        COUNTS_PATH.write_text(
            json.dumps(counts_index, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
            newline="\n",
        )


def main():
    report = {"removed_total": 0, "municipalities": {}}
    for code, rule in KNOWN_OUTLIER_RULES.items():
        path = MUNICIPALITY_DIR / f"{code}.geojson"
        data = json.loads(path.read_text(encoding="utf-8"))
        kept = []
        removed = []
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            coord = feature_anchor(feature)
            is_target_layer = props.get("layer_id") in rule["layers"]
            is_outlier_coord = coord and any(in_box(coord, box) for box in rule["coordinate_boxes"])
            if is_target_layer and is_outlier_coord:
                removed.append(
                    {
                        "name": props.get("name"),
                        "address": props.get("address"),
                        "layer_id": props.get("layer_id"),
                        "coordinates": coord,
                    }
                )
            else:
                kept.append(feature)

        if removed:
            data["features"] = kept
            refresh_counts(data)
            path.write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
                newline="\n",
            )
            update_indexes(code, data)

        report["removed_total"] += len(removed)
        report["municipalities"][code] = {
            "pref": data.get("pref"),
            "city": data.get("city"),
            "reason": rule["reason"],
            "removed_count": len(removed),
            "removed": removed,
        }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps({"removed_total": report["removed_total"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
