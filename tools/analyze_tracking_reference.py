"""Inspect a separately downloaded SkillCorner tracking JSONL sample.

No source rows are stored by this project. This utility reports broad motion
statistics for reproducibility and can read a complete file or a byte-range
prefix ending with a partial JSON line.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path


def inspect(path: Path) -> dict:
    frames = {}
    detected = players = 0
    with path.open() as file:
        for line in file:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                break
            if row.get("period") != 1 or len(row.get("player_data", [])) != 22:
                continue
            frames[row["frame"]] = {p["player_id"]: p for p in row["player_data"]}
            detected += sum(p["is_detected"] for p in row["player_data"])
            players += 22
    steps = []
    for number, a in frames.items():
        b = frames.get(number + 10)
        if b:
            steps.extend(math.dist((p["x"], p["y"]),
                                   (b[id]["x"], b[id]["y"]))
                         for id, p in a.items() if id in b)
    steps.sort()
    if not steps:
        raise ValueError("No comparable tracking frames found")
    return {"usable_frames": len(frames),
            "detected_player_fraction": round(detected / players, 3),
            "one_second_player_displacement_median_m": round(statistics.median(steps), 2),
            "one_second_player_displacement_p90_m": round(steps[int(.9 * (len(steps)-1))], 2),
            "one_second_player_displacement_p99_m": round(steps[int(.99 * (len(steps)-1))], 2)}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tools/analyze_tracking_reference.py PATH_TO_JSONL")
    for key, value in inspect(Path(sys.argv[1])).items():
        print(f"{key}: {value}")
