"""Deterministic evidence packets emitted only after their events are complete."""

from __future__ import annotations

from simulation import EVENTS


def build_candidates(events: list[dict] = EVENTS) -> list[dict]:
    baseline = [e for e in events if e["t"] < 24]
    pressing = [e for e in events if 24 <= e["t"] < 40]
    response = [e for e in events if 44 <= e["t"] < 64]

    high_pressures = [e for e in pressing if e["type"] == "pressure"
                      and e["x"] < -17.5]
    baseline_pressures = [e for e in baseline if e["type"] == "pressure"
                          and e["x"] < -17.5]
    recoveries = [e for e in pressing if e["type"] == "recovery"
                  and e["team"] == "Red" and e["x"] < -17.5]
    failed_exits = [e for e in pressing if e["team"] == "Blue"
                    and e["type"] == "pass" and e["outcome"] != "complete"
                    and e["x"] < -17.5]
    forward = [e for e in response if e["t"] >= 48 and e["team"] == "Blue"
               and e["type"] == "pass" and e["outcome"] == "complete"
               and e["end"][0] - e["x"] >= 12]

    candidates = []
    if len(high_pressures) >= 2 and recoveries and failed_exits:
        evidence = high_pressures + recoveries + failed_exits
        candidates.append({
            "id": "press_turn", "trigger_t": recoveries[-1]["t"] + .1,
            "kind": "pressure_turn", "focus_event_id": recoveries[-1]["id"],
            "evidence_ids": [e["id"] for e in evidence],
            "facts": {"baseline_high_pressures": len(baseline_pressures),
                      "press_window_high_pressures": len(high_pressures),
                      "red_high_recoveries": len(recoveries),
                      "blue_failed_exits": len(failed_exits),
                      "zone": "Blue defensive third",
                      "observation": "Blue lost possession near its own goal"},
        })
    if len(forward) >= 2 and candidates:
        evidence = forward[:2]
        candidates.append({
            "id": "blue_escape", "trigger_t": round(evidence[-1]["t"] + evidence[-1]["duration"] + .1, 1),
            "kind": "blue_escape", "focus_event_id": evidence[-1]["id"],
            "evidence_ids": [e["id"] for e in evidence],
            "facts": {"blue_completed_forward_passes": len(evidence),
                      "minimum_advance_metres": 12,
                      "red_high_recoveries_since_restart": 0,
                      "observation": "Blue advanced through two completed passes after restarting"},
        })
    return candidates


CANDIDATES = build_candidates()
