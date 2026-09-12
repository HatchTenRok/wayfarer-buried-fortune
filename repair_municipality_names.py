import json
from pathlib import Path


CORRECTIONS = {
    "01220": ("士別市朝日町中央13区", "士別市"),
    "13213": ("東村", "東村山市"),
    "17212": ("野々市市三納18街区", "野々市市"),
}


def write_json(path: Path, data: object, *, pretty: bool = False) -> None:
    kwargs = {"ensure_ascii": False}
    if pretty:
        kwargs["indent"] = 2
    else:
        kwargs["separators"] = (",", ":")
    path.write_text(json.dumps(data, **kwargs), encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parent
    municipalities_path = root / "data" / "municipalities.json"
    municipalities = json.loads(municipalities_path.read_text(encoding="utf-8"))

    changed_search_records = 0
    changed_feature_properties = 0
    for item in municipalities:
        code = str(item.get("municipality_code", ""))
        correction = CORRECTIONS.get(code)
        if not correction:
            continue
        old_name, new_name = correction
        data_changed = False
        if item.get("city") == old_name:
            item["city"] = new_name
            item["label"] = f"{item.get('pref', '')} {new_name}".strip()
            changed_search_records += 1

        data_path = root / "data" / "by_municipality" / f"{code}.geojson"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        if data.get("city") == old_name:
            data["city"] = new_name
            data_changed = True
        comment = data.get("display_comment")
        if isinstance(comment, str) and old_name in comment:
            data["display_comment"] = comment.replace(old_name, new_name)
            data_changed = True
        for feature in data.get("features", []):
            properties = feature.get("properties", {})
            if properties.get("municipality_name") == old_name:
                properties["municipality_name"] = new_name
                changed_feature_properties += 1
                data_changed = True
        if data_changed:
            write_json(data_path, data)

    write_json(municipalities_path, municipalities)
    report = {
        "corrections": {
            code: {"from": old_name, "to": new_name}
            for code, (old_name, new_name) in CORRECTIONS.items()
        },
        "changed_search_records": changed_search_records,
        "changed_feature_properties": changed_feature_properties,
    }
    write_json(root / "reports" / "municipality_name_repair.json", report, pretty=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
