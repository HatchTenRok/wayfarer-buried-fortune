#!/usr/bin/env python3
"""Remove obsolete history map layers and move industrial names into profile cards."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_ver3_integration import build_wiki_summary_title


REMOVED_LAYERS = {"historical_place_names", "industrial_heritage_reference"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_compact(path: Path, payload: Any) -> None:
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    temporary.replace(path)


def clean_name(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    history_dir = root / "data" / "history_by_municipality"
    profile_dir = root / "data" / "profiles"
    industrial_names: dict[str, list[str]] = defaultdict(list)
    removed_by_layer: Counter[str] = Counter()
    features_before = 0
    features_after = 0
    history_files_changed = 0
    previous_report_path = root / "history_layer_cleanup_report.json"
    previous_report = load(previous_report_path) if previous_report_path.is_file() else {}

    for path in sorted(history_dir.glob("*.geojson")):
        payload = load(path)
        original = payload.get("features", [])
        kept = []
        for feature in original:
            props = feature.get("properties") or {}
            layer_id = props.get("layer_id")
            if layer_id in REMOVED_LAYERS:
                removed_by_layer[layer_id] += 1
                if layer_id == "industrial_heritage_reference":
                    name = clean_name(props.get("name"))
                    if name:
                        industrial_names[path.stem].append(f"{name}（産業遺産）")
                continue
            kept.append(feature)

        features_before += len(original)
        features_after += len(kept)
        if len(kept) == len(original):
            continue
        history_files_changed += 1
        counts = Counter(
            (feature.get("properties") or {}).get("layer_id", "unknown")
            for feature in kept
        )
        payload["features"] = kept
        payload["layer_counts"] = dict(sorted(counts.items()))
        payload["total_features"] = len(kept)
        if args.apply:
            write_compact(path, payload)

    profiles_changed = 0
    industrial_names_added = 0
    industrial_names_retained = 0
    industrial_names_removed_as_existing_landmarks = 0
    municipalities_with_industrial = 0
    for path in sorted(profile_dir.glob("*.json")):
        profile = load(path)
        changed = False
        groups = profile.get("radar_groups") or []
        for group in groups:
            metrics = group.get("metrics") or []
            filtered = [metric for metric in metrics if metric.get("id") != "industrial"]
            if len(filtered) != len(metrics):
                group["metrics"] = filtered
                changed = True

        cards = profile.setdefault("culture_cards", {})
        landmarks = list(cards.get("tourism_landmarks") or [])
        additions = []
        for item in industrial_names.get(path.stem, []):
            normalized = clean_name(item)
            if normalized:
                additions.append(normalized)
        if additions:
            landmarks.extend(additions)
            industrial_names_added += len(additions)

        deduplicated_landmarks = []
        seen_landmark_names: set[str] = set()
        municipality_has_industrial = False
        for item in landmarks:
            cleaned = clean_name(item)
            is_industrial = cleaned.endswith("（産業遺産）")
            base_name = cleaned.removesuffix("（産業遺産）").strip()
            if not base_name:
                continue
            if base_name in seen_landmark_names:
                if is_industrial:
                    industrial_names_removed_as_existing_landmarks += 1
                continue
            seen_landmark_names.add(base_name)
            deduplicated_landmarks.append(cleaned)
            if is_industrial:
                industrial_names_retained += 1
                municipality_has_industrial = True
        if municipality_has_industrial:
            municipalities_with_industrial += 1
        if deduplicated_landmarks != cards.get("tourism_landmarks", []):
            cards["tourism_landmarks"] = deduplicated_landmarks
            changed = True

        notes = [
            str(note)
            for note in profile.get("data_notes", [])
            if "歴史地名" not in str(note) and "産業遺産" not in str(note)
        ]
        if municipality_has_industrial:
            notes.append("産業遺産は名称情報のみを観光・歴史名所へ収録し、地図上のピンは表示していません。")
        if notes != profile.get("data_notes", []):
            profile["data_notes"] = notes
            changed = True

        new_title = build_wiki_summary_title(cards, profile.get("display_comment_enriched", ""))
        if profile.get("wiki_summary_title") != new_title:
            profile["wiki_summary_title"] = new_title
            changed = True
        if changed:
            profiles_changed += 1
            if args.apply:
                write_compact(path, profile)

    if sum(removed_by_layer.values()):
        cumulative_removed = removed_by_layer
        original_features = features_before
    else:
        cumulative_removed = Counter(previous_report.get("removed_by_layer") or {})
        original_features = int(previous_report.get("features_before") or features_before)
    report = {
        "mode": "apply" if args.apply else "dry-run",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "history_files_changed": max(history_files_changed, int(previous_report.get("history_files_changed") or 0)),
        "features_before": original_features,
        "features_after": features_after,
        "features_removed": original_features - features_after,
        "removed_by_layer": dict(sorted(cumulative_removed.items())),
        "profiles_changed": profiles_changed,
        "industrial_names_added": max(industrial_names_added, int(previous_report.get("industrial_names_added") or 0)),
        "industrial_names_retained": industrial_names_retained,
        "industrial_names_removed_as_existing_landmarks": industrial_names_removed_as_existing_landmarks,
        "municipalities_with_industrial_names": municipalities_with_industrial,
    }

    if args.apply:
        integration_report_path = root / "ver3_integration_report.json"
        if integration_report_path.is_file():
            integration_report = load(integration_report_path)
            integration_report["history_feature_count"] = features_after
            integration_report["history_bytes"] = sum(
                path.stat().st_size for path in history_dir.glob("*.geojson")
            )
            integration_report["post_process"] = report
            write_compact(integration_report_path, integration_report)
        write_compact(root / "history_layer_cleanup_report.json", report)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
