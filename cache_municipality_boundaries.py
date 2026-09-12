import json
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path


SERVICE_URL = (
    "https://services.arcgis.com/wlVTGRSYTzAbjjiC/arcgis/rest/services/"
    "municipalityboundaries2020/FeatureServer/0/query"
)


def main() -> None:
    root = Path(__file__).resolve().parent
    output_dir = root / "data" / "boundaries"
    report_path = root / "reports" / "municipality_boundary_cache.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    params = urllib.parse.urlencode(
        {
            "where": "1=1",
            "outFields": "JCODE",
            "returnGeometry": "true",
            "outSR": "4326",
            "geometryPrecision": "6",
            "maxAllowableOffset": "0.00005",
            "resultRecordCount": "2000",
            "f": "geojson",
        }
    )
    request = urllib.request.Request(
        f"{SERVICE_URL}?{params}",
        headers={"User-Agent": "WayfarerBuriedFortune/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        source = json.load(response)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for feature in source.get("features", []):
        code = str(feature.get("properties", {}).get("JCODE", "")).zfill(5)
        geometry = feature.get("geometry")
        if len(code) != 5 or not geometry:
            continue
        grouped[code].append(
            {
                "type": "Feature",
                "properties": {"municipality_code": code},
                "geometry": geometry,
            }
        )

    for code, features in grouped.items():
        collection = {"type": "FeatureCollection", "features": features}
        (output_dir / f"{code}.geojson").write_text(
            json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    report = {
        "source": SERVICE_URL,
        "source_attribution": "(c) Esri Japan",
        "source_description": (
            "ESRIジャパン株式会社の全国市区町村界データ（2020年版）。"
            "国土地理院の数値地図（国土基本情報）を加工・編集。"
        ),
        "municipality_files": len(grouped),
        "source_features": len(source.get("features", [])),
        "geometry_precision": 6,
        "max_allowable_offset_degrees": 0.00005,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
