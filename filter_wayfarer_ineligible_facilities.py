#!/usr/bin/env python3
"""Audit and remove facility POIs excluded from this Wayfarer dataset.

Dry-run is the default. Pass --apply to rewrite the runtime municipality files
and their two count indexes. Matching is intentionally based on the displayed
facility name because the lite runtime package no longer retains source dataset
IDs or source-specific facility type codes.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


TARGET_LAYERS = {
    "cafe_restaurant",
    "cultural_facilities",
    "public_facilities",
    "tourism_resources",
}


RULES = (
    (
        "school_university",
        re.compile(
            r"学校|學校|小學校|中學校|高等学校|高校|大学|短期大学|短大|大学院|大学校|"
            r"高等専門学校|高専|専門学校|専修学校|各種学校|予備校|学院|学園|"
            r"小学部|中学部|高等部|義務教育|中等教育|一貫校|分校|校舎|学生寮|"
            r"キャンパス|school|university|college|academy",
            re.IGNORECASE,
        ),
    ),
    (
        "childcare",
        re.compile(
            r"幼稚|幼児園|幼保園|保育|託児|"
            r"こども園|子ども園|子供園|児童|乳児|幼児|学童|子育て|"
            r"放課後(?:児童|等デイサービス)|療育(?:園|施設|センター)|"
            r"kindergarten|nursery|day[ -]?care|child[ -]?care",
            re.IGNORECASE,
        ),
    ),
    (
        "special_support",
        re.compile(
            r"特別支援|養護学校|盲学校|聾学校|ろう学校|障害児|障がい児|発達支援センター",
            re.IGNORECASE,
        ),
    ),
    (
        "disability_facility",
        re.compile(
            r"(?:障害|障がい|障碍)(?:者|児)|身体障害|知的障害|精神障害|"
            r"視覚障害|聴覚障害|視聴覚障|障害福祉|障がい福祉|"
            r"盲人|ろうあ|聾唖|点字図書館|福祉作業所|"
            r"就労(?:移行|継続)支援|生活介護事業所",
            re.IGNORECASE,
        ),
    ),
    (
        "elder_care",
        re.compile(
            r"老人|高齢者|"
            r"特別養護|養護老人|軽費老人|介護|有料老人|老健|"
            r"介護センター|介護事業所|在宅介護|訪問介護|通所介護|デイサービス|デイケア|"
            r"ケアハウス|ケアホーム|ケアセンター|グループホーム|シルバーハウス|"
            r"サービス付き?高齢者向け?住宅|サ高住|"
            r"nursing[ -]?home|senior[ -]?(?:home|care)",
            re.IGNORECASE,
        ),
    ),
    (
        "medical",
        re.compile(
            r"病院|医院|診療所|クリニック|医療|医科|メディカル(?:センター|クリニック)|"
            r"健診|検診|保健|救命|救急|"
            r"療養所|助産院|ホスピス|透析センター|リハビリテーション(?:病院|センター)|"
            r"リハビリセンター|歯科|眼科|耳鼻咽喉科|産婦人科|整形外科|"
            r"(?:内科|外科|小児科|皮膚科|泌尿器科|精神科|心療内科)(?:医院|診療所|クリニック)?$|"
            r"調剤|薬局|薬店|hospital|clinic|medical|hospice",
            re.IGNORECASE,
        ),
    ),
)


SECOND_PASS_TERMS = re.compile(
    r"学校|學校|幼稚|幼児|保育|託児|こども園|子ども園|子供園|児童|乳児|学童|子育て|"
    r"大学|短大|高専|専門学校|専修学校|学院|学園|キャンパス|学生寮|"
    r"障害者|障がい者|障碍者|障害児|障がい児|身体障害|知的障害|精神障害|視覚障害|聴覚障害|"
    r"老人|高齢者|介護|老健|ケアハウス|ケアホーム|ケアセンター|グループホーム|デイサービス|デイケア|"
    r"病院|医院|診療所|クリニック|医療|医科|保健|健診|検診|救急|療養|ホスピス|歯科|眼科|耳鼻|産婦人科|"
    r"整形外科|内科|外科|小児科|皮膚科|泌尿器科|精神科|心療内科|薬局|"
    r"school|university|college|kindergarten|nursery|day[ -]?care|hospital|clinic|medical",
    re.IGNORECASE,
)


def normalized(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def matching_rules(name: str) -> list[str]:
    return [rule_name for rule_name, pattern in RULES if pattern.search(name)]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def sorted_counts(features: list[dict]) -> dict[str, int]:
    counts = Counter(
        feature.get("properties", {}).get("layer_id", "unknown")
        for feature in features
    )
    return dict(sorted(counts.items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    data_dir = root / "data" / "by_municipality"
    files = sorted(data_dir.glob("*.geojson"))
    if not files:
        raise SystemExit(f"No municipality GeoJSON found under {data_dir}")

    removed_by_rule = Counter()
    removed_by_layer = Counter()
    removed_by_source = Counter()
    removed_by_municipality = Counter()
    samples_by_rule: dict[str, list[dict]] = defaultdict(list)
    updated_payloads: dict[str, dict] = {}
    municipality_counts: dict[str, dict] = {}
    layer_totals = Counter()
    total_before = 0
    total_after = 0

    for path in files:
        payload = load_json(path)
        kept: list[dict] = []
        removed_here = 0
        total_before += len(payload.get("features", []))

        for feature in payload.get("features", []):
            props = feature.get("properties", {})
            name = normalized(props.get("name"))
            layer_id = normalized(props.get("layer_id")) or "unknown"
            rules = matching_rules(name) if layer_id in TARGET_LAYERS else []
            if not rules:
                kept.append(feature)
                continue

            removed_here += 1
            source = normalized(props.get("source")) or "unknown"
            removed_by_layer[layer_id] += 1
            removed_by_source[source] += 1
            for rule_name in rules:
                removed_by_rule[rule_name] += 1
                if len(samples_by_rule[rule_name]) < 25:
                    samples_by_rule[rule_name].append(
                        {
                            "municipality_code": payload.get("municipality_code"),
                            "layer_id": layer_id,
                            "name": name,
                            "source": source,
                        }
                    )

        code = str(payload.get("municipality_code") or path.stem)
        if removed_here:
            removed_by_municipality[code] = removed_here

        counts = sorted_counts(kept)
        payload["features"] = kept
        payload["layer_counts"] = counts
        payload["total_features"] = len(kept)
        updated_payloads[code] = payload
        municipality_counts[code] = counts
        layer_totals.update(counts)
        total_after += len(kept)

    # Independent second-pass audit against every name that would remain.
    suspicious_remaining: list[dict] = []
    suspicious_by_layer = Counter()
    suspicious_count = 0
    for code, payload in updated_payloads.items():
        for feature in payload.get("features", []):
            props = feature.get("properties", {})
            name = normalized(props.get("name"))
            layer_id = normalized(props.get("layer_id")) or "unknown"
            if layer_id in TARGET_LAYERS and SECOND_PASS_TERMS.search(name):
                suspicious_count += 1
                suspicious_by_layer[layer_id] += 1
                if len(suspicious_remaining) < 200:
                    suspicious_remaining.append(
                        {
                            "municipality_code": code,
                            "layer_id": props.get("layer_id"),
                            "name": name,
                            "source": props.get("source"),
                        }
                    )

    report = {
        "mode": "apply" if args.apply else "dry-run",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "municipality_files": len(files),
        "features_before": total_before,
        "features_removed": total_before - total_after,
        "features_after": total_after,
        "municipalities_changed": len(removed_by_municipality),
        "removed_by_rule": dict(sorted(removed_by_rule.items())),
        "removed_by_layer": dict(sorted(removed_by_layer.items())),
        "removed_by_source": dict(sorted(removed_by_source.items())),
        "layer_totals_after": dict(sorted(layer_totals.items())),
        "second_pass_suspicious_remaining_count": suspicious_count,
        "second_pass_suspicious_remaining_by_layer": dict(sorted(suspicious_by_layer.items())),
        "second_pass_suspicious_remaining_samples": suspicious_remaining,
        "samples_by_rule": dict(samples_by_rule),
    }

    if args.report:
        write_json(args.report, report)

    if args.apply:
        for code, payload in updated_payloads.items():
            write_json(data_dir / f"{code}.geojson", payload)

        municipalities_path = root / "data" / "municipalities.json"
        municipalities = load_json(municipalities_path)
        for municipality in municipalities:
            code = str(municipality.get("municipality_code"))
            municipality["feature_count"] = sum(municipality_counts.get(code, {}).values())
        write_json(municipalities_path, municipalities)

        index_path = root / "indexes" / "municipality_layer_counts.json"
        index = load_json(index_path)
        index["generated_at"] = datetime.now(timezone.utc).isoformat()
        index["by_municipality"] = {
            code: {
                "municipality_code": code,
                "layers": municipality_counts[code],
                "total": sum(municipality_counts[code].values()),
            }
            for code in sorted(municipality_counts)
        }
        index["layer_totals"] = dict(sorted(layer_totals.items()))
        write_json(index_path, index)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

