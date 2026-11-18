"""Summarize comparable native observations from the launch kit's CSV."""

import argparse
import csv
import json
from collections import defaultdict
from math import isfinite
from pathlib import Path
from statistics import median

from pipeline import METRICS_FIELDS, PLATFORMS, parse_time

COUNTS = ("views", "likes", "comments", "shares", "saves", "follower_count")


def summarize(stream, synthetic=False):
    rows = csv.DictReader(stream)
    if not set(METRICS_FIELDS).issubset(rows.fieldnames or ()):
        raise ValueError("Use the kit's metrics CSV header")
    seen = {}
    for row in rows:
        network, native_id, pillar = row["platform"], row["native_id"], row["pillar"]
        if network not in PLATFORMS or not native_id or not pillar:
            raise ValueError("Platform, native ID and pillar are required")
        expected_source = {"synthetic"} if synthetic else {"native", "native_export"}
        if row["source"] not in expected_source:
            raise ValueError("Native and synthetic observations must be processed separately")
        window = int(row["window_hours"])
        if window not in {12, 24, 72}:
            raise ValueError("Expected a 12, 24 or 72 hour window")
        published, captured = parse_time(row["published_at"]), parse_time(row["captured_at"])
        if not window <= (captured - published).total_seconds() / 3600 < window + 6:
            raise ValueError("Observation timestamp outside its six-hour collection window")
        values = {field: int(row[field]) if row[field] else None for field in COUNTS}
        retention = float(row["retention_percent"]) if row["retention_percent"] else None
        if any(value is not None and value < 0 for value in values.values()):
            raise ValueError("Counts must be nonnegative")
        if retention is not None and (not isfinite(retention) or retention < 0):
            raise ValueError("Retention must be a finite nonnegative value")
        values["retention_percent"] = retention
        key = (network, native_id, window)
        previous = seen.get(key)
        if previous and (previous[1] != pillar or previous[3] != published):
            raise ValueError("Conflicting identity for the same native post")
        if previous and previous[0] == captured and previous[2] != values:
            raise ValueError("Conflicting observations with the same timestamp")
        if not previous or previous[0] < captured:
            seen[key] = (captured, pillar, values, published)

    grouped = defaultdict(list)
    for (platform, _, window), (_, pillar, values, _) in seen.items():
        grouped[(platform, pillar, window)].append(values)
    result = []
    for (platform, pillar, window), values in sorted(grouped.items()):
        aggregated = {}
        for metric in (*COUNTS, "retention_percent"):
            observed = [row[metric] for row in values if row[metric] is not None]
            aggregated[metric] = {"n": len(observed), "median": median(observed) if observed else None}
        result.append({
            "platform": platform, "pillar": pillar, "window_hours": window, "posts": len(values),
            "comparison": "too_early" if window < 24 else "descriptive_only",
            "metrics": aggregated,
        })
    return {"mode": "SYNTHETIC" if synthetic else "NATIVE_CSV", "observations": len(seen), "groups": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    with args.csv_path.open(newline="", encoding="utf-8-sig") as stream:
        print(json.dumps(summarize(stream, args.synthetic), indent=2))


if __name__ == "__main__":
    main()
