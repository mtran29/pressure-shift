"""Synthetic event stream and transparent pressure-shift detection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from random import Random


@dataclass(frozen=True)
class Event:
    id: str
    second: int
    minute: str
    team: str
    player: str
    type: str
    x: int
    y: int
    end_x: int | None = None
    end_y: int | None = None
    outcome: str | None = None
    phase: str = ""

    def public(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Insight:
    id: str
    trigger_second: int
    trigger_event_id: str
    kind: str
    facts: dict
    evidence_ids: tuple[str, ...]

    def public(self) -> dict:
        return asdict(self)


RED = "Red FC"
BLUE = "Blue FC"


def _stamp(second: int) -> str:
    return f"{second // 60:02d}:{second % 60:02d}"


def generate_match(seed: int = 7) -> list[Event]:
    """Create a football-realistic but wholly fictional match segment.

    Coordinates run 0..100 left to right. Blue attacks right; Red attacks left.
    A high Red recovery therefore occurs at x >= 67.
    """
    rng = Random(seed)
    events: list[Event] = []

    def add(second: int, team: str, player: str, kind: str, x: int, y: int,
            end_x: int | None = None, end_y: int | None = None,
            outcome: str | None = None, phase: str = "") -> None:
        events.append(Event(f"E{len(events) + 1:03d}", second, _stamp(second), team,
                            player, kind, x, y, end_x, end_y, outcome, phase))

    # 20:00–24:59: Blue progresses without much high pressure.
    for i in range(11):
        t = 1205 + i * 25
        x = 15 + (i % 3) * 12
        y = 25 + (i % 4) * 15
        add(t, BLUE, ["B. Vale", "M. Chen", "A. Noor"][i % 3], "pass", x, y,
            min(x + 18, 70), min(y + rng.choice([-7, 0, 7]), 90), "complete", "baseline")
    add(1450, RED, "R. Silva", "pressure", 74, 44, phase="baseline")

    # 25:00–29:59: Red's press creates repeated disruption in Blue's own third.
    for i in range(7):
        t = 1510 + i * 37
        y = 18 + (i * 11) % 63
        add(t, RED, ["R. Silva", "T. Okafor", "J. Kim"][i % 3], "pressure",
            72 + (i % 3) * 6, y, phase="press")
        if i in (1, 3, 5, 6):
            add(t + 5, BLUE, ["B. Vale", "M. Chen"][i % 2], "pass", 80, y,
                62, y + 4, "incomplete", "press")
        if i in (2, 4, 6):
            add(t + 9, RED, ["R. Silva", "T. Okafor", "J. Kim"][i % 3],
                "recovery", 76, y + 2, outcome="won", phase="press")
            add(t + 10, RED, ["R. Silva", "T. Okafor", "J. Kim"][i % 3],
                "possession_change", 76, y + 2, outcome="won", phase="press")
        if i in (3, 5):
            add(t + 3, RED, "J. Kim", "tackle", 73, y, outcome="contested", phase="press")
    add(1788, RED, "R. Silva", "pass", 71, 50, 61, 46, "complete", "press")

    # 30:00–34:59: Blue plays forward through pressure, reducing high turnovers.
    for i in range(9):
        t = 1810 + i * 29
        x = 18 + (i % 2) * 14
        y = 19 + (i * 9) % 61
        if i in (1, 4):
            add(t - 4, RED, "T. Okafor", "pressure", 75, y, phase="response")
        add(t, BLUE, ["B. Vale", "M. Chen", "A. Noor"][i % 3], "pass", x, y,
            x + 23, min(y + rng.choice([-6, 0, 6]), 90), "complete", "response")
    add(2090, BLUE, "A. Noor", "shot", 83, 51, 100, 50, "off_target", "response")
    return sorted(events, key=lambda e: (e.second, e.id))


def _window(events: list[Event], start: int, end: int) -> list[Event]:
    return [e for e in events if start <= e.second < end]


def _count(events: list[Event], kind: str, team: str,
           outcome: str | None = None, min_x: int | None = None) -> int:
    return sum(e.type == kind and e.team == team
               and (outcome is None or e.outcome == outcome)
               and (min_x is None or e.x >= min_x) for e in events)


def detect_insights(events: list[Event]) -> list[Insight]:
    """Derive two insights from window comparisons; no language model decisions."""
    baseline = _window(events, 1200, 1500)
    press = _window(events, 1500, 1800)
    response = _window(events, 1800, 2100)
    found: list[Insight] = []

    high_before = _count(baseline, "recovery", RED, min_x=67)
    high_press = _count(press, "recovery", RED, min_x=67)
    pressures_before = _count(baseline, "pressure", RED, min_x=67)
    pressures_press = _count(press, "pressure", RED, min_x=67)
    failed_exits = _count(press, "pass", BLUE, outcome="incomplete", min_x=67)
    if high_press >= 3 and high_press - high_before >= 2 and pressures_press >= 5:
        evidence = tuple(e.id for e in press if e.type in ("recovery", "pressure")
                         and e.team == RED and e.x >= 67)
        evidence += tuple(e.id for e in press if e.team == BLUE and e.type == "pass"
                          and e.outcome == "incomplete" and e.x >= 67)
        found.append(Insight(
            "press_surge", press[-1].second, press[-1].id, "pressure_surge",
            {"window": "25:00–29:59", "previous_window": "20:00–24:59",
             "red_high_recoveries": high_press, "previous_high_recoveries": high_before,
             "red_attacking_third_pressures": pressures_press,
             "previous_pressures": pressures_before, "blue_failed_defensive_exits": failed_exits},
            evidence))

    high_response = _count(response, "recovery", RED, min_x=67)
    blue_progressive = sum(e.team == BLUE and e.type == "pass" and
                           e.outcome == "complete" and e.end_x is not None and
                           e.end_x - e.x >= 20 for e in response)
    if found and high_response < high_press and blue_progressive >= 5:
        evidence = tuple(e.id for e in response if e.team == BLUE and
                         e.type == "pass" and e.outcome == "complete" and
                         e.end_x is not None and e.end_x - e.x >= 20)
        found.append(Insight(
            "press_response", response[-1].second, response[-1].id, "press_response",
            {"window": "30:00–34:59", "previous_window": "25:00–29:59",
             "red_high_recoveries": high_response,
             "previous_high_recoveries": high_press,
             "blue_completed_progressive_passes": blue_progressive,
             "progressive_pass_definition": "completed pass advancing at least 20% of pitch length"},
            evidence))
    return found


EVENTS = generate_match()
INSIGHTS = detect_insights(EVENTS)
