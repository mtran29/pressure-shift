"""Fictional, possession-linked event replay and transparent pressure detection.

Coordinates are percentages of pitch length and width. Blue attacks right, so
Red's attacking third is Blue's defensive third (x <= 33).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


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
    recipient: str | None = None
    possession_id: str | None = None

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


def generate_match() -> list[Event]:
    """Script a five-minute passage with connected passes and explicit restarts.

    Times are match-clock seconds. Intervening seconds are ordinary movement
    without a tagged event; this is event data, not video tracking.
    """
    events: list[Event] = []

    def add(second: int, team: str, player: str, kind: str, x: int, y: int,
            end_x: int | None = None, end_y: int | None = None,
            outcome: str | None = None, possession_id: str | None = None,
            recipient: str | None = None) -> None:
        phase = "baseline" if second < 3700 else "press" if second < 3800 else "response"
        events.append(Event(f"E{len(events)+1:03d}", second, _stamp(second), team,
                            player, kind, x, y, end_x, end_y, outcome, phase,
                            recipient, possession_id))

    def chain(team: str, possession_id: str, steps: list[tuple]) -> None:
        """Each step is (second, passer, receiver, start, end, outcome)."""
        for second, passer, receiver, start, end, outcome in steps:
            add(second, team, passer, "pass", *start, *end, outcome,
                possession_id, receiver)

    # Blue build-up: one continuous possession, then a shot and goalkeeper restart.
    add(3600, BLUE, "B. Vale", "goal_kick", 7, 50, outcome="taken", possession_id="B1")
    chain(BLUE, "B1", [
        (3603, "B. Vale", "M. Chen", (7, 50), (17, 43), "complete"),
        (3607, "M. Chen", "A. Noor", (17, 43), (25, 30), "complete"),
        (3612, "A. Noor", "M. Chen", (25, 30), (33, 42), "complete"),
        (3616, "M. Chen", "S. Costa", (33, 42), (45, 30), "complete"),
        (3621, "S. Costa", "A. Noor", (45, 30), (56, 43), "complete"),
        (3626, "A. Noor", "D. Park", (56, 43), (66, 31), "complete"),
        (3631, "D. Park", "S. Costa", (66, 31), (76, 43), "complete"),
    ])
    add(3609, RED, "R. Silva", "pressure", 25, 30, possession_id="B1")
    add(3637, BLUE, "S. Costa", "shot", 76, 43, 100, 47, "saved", "B1")
    add(3638, RED, "L. Reed", "recovery", 93, 50, outcome="won", possession_id="R1")
    add(3638, RED, "L. Reed", "possession_change", 93, 50, outcome="won", possession_id="R1")
    chain(RED, "R1", [
        (3646, "L. Reed", "J. Kim", (93, 50), (81, 58), "complete"),
        (3652, "J. Kim", "T. Okafor", (81, 58), (69, 70), "complete"),
        (3658, "T. Okafor", "R. Silva", (69, 70), (59, 56), "complete"),
        (3664, "R. Silva", "J. Kim", (59, 56), (47, 68), "complete"),
        (3670, "J. Kim", "T. Okafor", (47, 68), (36, 53), "complete"),
        (3675, "T. Okafor", "R. Silva", (36, 53), (27, 47), "complete"),
    ])
    add(3681, RED, "R. Silva", "shot", 27, 47, 0, 50, "saved", "R1")
    add(3682, BLUE, "B. Vale", "recovery", 7, 50, outcome="won", possession_id="B2")
    add(3682, BLUE, "B. Vale", "possession_change", 7, 50, outcome="won", possession_id="B2")
    chain(BLUE, "B2", [
        (3686, "B. Vale", "M. Chen", (7, 50), (17, 43), "complete"),
        (3691, "M. Chen", "A. Noor", (17, 43), (26, 34), "complete"),
        (3696, "A. Noor", "M. Chen", (26, 34), (31, 45), "complete"),
        (3705, "M. Chen", "B. Vale", (31, 45), (22, 50), "complete"),
        (3709, "B. Vale", "A. Noor", (22, 50), (28, 39), "incomplete"),
    ])
    add(3701, RED, "R. Silva", "pressure", 31, 45, possession_id="B2")
    add(3707, RED, "T. Okafor", "pressure", 22, 50, possession_id="B2")
    add(3710, RED, "R. Silva", "recovery", 28, 39, outcome="won", possession_id="R2")
    add(3710, RED, "R. Silva", "possession_change", 28, 39, outcome="won", possession_id="R2")
    chain(RED, "R2", [
        (3713, "R. Silva", "J. Kim", (28, 39), (20, 48), "complete"),
    ])
    add(3719, RED, "J. Kim", "shot", 20, 48, 0, 44, "off_target", "R2")

    add(3732, BLUE, "B. Vale", "goal_kick", 7, 50, outcome="taken", possession_id="B3")
    chain(BLUE, "B3", [
        (3735, "B. Vale", "M. Chen", (7, 50), (17, 56), "complete"),
        (3740, "M. Chen", "A. Noor", (17, 56), (25, 65), "complete"),
        (3745, "A. Noor", "D. Park", (25, 65), (29, 55), "incomplete"),
    ])
    add(3738, RED, "J. Kim", "pressure", 17, 56, possession_id="B3")
    add(3743, RED, "T. Okafor", "pressure", 25, 65, possession_id="B3")
    add(3744, RED, "T. Okafor", "tackle", 25, 65, outcome="contested", possession_id="B3")
    add(3746, RED, "J. Kim", "recovery", 29, 55, outcome="won", possession_id="R3")
    add(3746, RED, "J. Kim", "possession_change", 29, 55, outcome="won", possession_id="R3")
    chain(RED, "R3", [
        (3749, "J. Kim", "R. Silva", (29, 55), (21, 49), "complete"),
    ])
    add(3756, RED, "R. Silva", "shot", 21, 49, 0, 53, "off_target", "R3")

    add(3769, BLUE, "B. Vale", "goal_kick", 7, 50, outcome="taken", possession_id="B4")
    chain(BLUE, "B4", [
        (3772, "B. Vale", "M. Chen", (7, 50), (17, 44), "complete"),
        (3777, "M. Chen", "A. Noor", (17, 44), (27, 34), "complete"),
        (3782, "A. Noor", "S. Costa", (27, 34), (39, 42), "complete"),
        (3786, "S. Costa", "D. Park", (39, 42), (52, 33), "complete"),
        (3790, "D. Park", "A. Noor", (52, 33), (65, 43), "complete"),
        (3794, "A. Noor", "S. Costa", (65, 43), (76, 47), "complete"),
    ])
    add(3775, RED, "R. Silva", "pressure", 17, 44, possession_id="B4")
    add(3780, RED, "T. Okafor", "pressure", 27, 34, possession_id="B4")
    add(3798, BLUE, "S. Costa", "shot", 76, 47, 100, 49, "off_target", "B4")

    add(3811, RED, "L. Reed", "goal_kick", 93, 50, outcome="taken", possession_id="R4")
    chain(RED, "R4", [
        (3814, "L. Reed", "J. Kim", (93, 50), (81, 60), "complete"),
        (3819, "J. Kim", "T. Okafor", (81, 60), (67, 71), "complete"),
        (3823, "T. Okafor", "R. Silva", (67, 71), (52, 58), "complete"),
        (3828, "R. Silva", "J. Kim", (52, 58), (36, 66), "complete"),
        (3833, "J. Kim", "T. Okafor", (36, 66), (29, 52), "complete"),
    ])
    add(3838, RED, "T. Okafor", "shot", 29, 52, 0, 52, "off_target", "R4")

    # Blue's response alternates a forward pass and a recycle in one possession.
    add(3848, BLUE, "B. Vale", "goal_kick", 7, 50, outcome="taken", possession_id="B5")
    chain(BLUE, "B5", [
        (3851, "B. Vale", "M. Chen", (7, 50), (30, 44), "complete"),
        (3856, "M. Chen", "A. Noor", (30, 44), (18, 56), "complete"),
        (3860, "A. Noor", "S. Costa", (18, 56), (43, 42), "complete"),
        (3864, "S. Costa", "M. Chen", (43, 42), (32, 54), "complete"),
        (3868, "M. Chen", "D. Park", (32, 54), (55, 42), "complete"),
        (3872, "D. Park", "S. Costa", (55, 42), (40, 55), "complete"),
        (3876, "S. Costa", "A. Noor", (40, 55), (64, 44), "complete"),
        (3880, "A. Noor", "D. Park", (64, 44), (52, 53), "complete"),
        (3884, "D. Park", "S. Costa", (52, 53), (76, 46), "complete"),
    ])
    add(3854, RED, "R. Silva", "pressure", 30, 44, possession_id="B5")
    add(3889, BLUE, "S. Costa", "shot", 76, 46, 100, 50, "saved", "B5")
    add(3890, RED, "L. Reed", "recovery", 93, 50, outcome="won", possession_id="R5")
    add(3890, RED, "L. Reed", "possession_change", 93, 50, outcome="won", possession_id="R5")
    chain(RED, "R5", [
        (3894, "L. Reed", "J. Kim", (93, 50), (81, 58), "complete"),
    ])
    return sorted(events, key=lambda e: (e.second, e.id))


def _window(events: list[Event], start: int, end: int) -> list[Event]:
    return [e for e in events if start <= e.second < end]


def _count(events: list[Event], kind: str, team: str,
           outcome: str | None = None, max_x: int | None = None) -> int:
    return sum(e.type == kind and e.team == team
               and (outcome is None or e.outcome == outcome)
               and (max_x is None or e.x <= max_x) for e in events)


def detect_insights(events: list[Event]) -> list[Insight]:
    """Raise insights from the event evidence, independent of generated language."""
    baseline = _window(events, 3600, 3700)
    press = _window(events, 3700, 3800)
    response = _window(events, 3800, 3900)
    found: list[Insight] = []

    high_before = _count(baseline, "recovery", RED, max_x=33)
    high_press = _count(press, "recovery", RED, max_x=33)
    pressures_before = _count(baseline, "pressure", RED, max_x=33)
    pressures_press = _count(press, "pressure", RED, max_x=33)
    failed_exits = _count(press, "pass", BLUE, outcome="incomplete", max_x=33)
    if press and high_press >= 2 and high_press - high_before >= 2 and pressures_press >= 5:
        evidence = tuple(e.id for e in press if e.team == RED and e.x <= 33
                         and e.type in ("recovery", "pressure"))
        evidence += tuple(e.id for e in press if e.team == BLUE and e.type == "pass"
                          and e.outcome == "incomplete" and e.x <= 33)
        found.append(Insight(
            "press_surge", press[-1].second, press[-1].id, "pressure_surge",
            {"window": "61:40–63:19", "previous_window": "60:00–61:39",
             "red_high_recoveries": high_press, "previous_high_recoveries": high_before,
             "red_attacking_third_pressures": pressures_press,
             "previous_pressures": pressures_before,
             "blue_failed_defensive_exits": failed_exits},
            evidence))

    high_response = _count(response, "recovery", RED, max_x=33)
    blue_progressive = sum(e.team == BLUE and e.type == "pass" and
                           e.outcome == "complete" and e.end_x is not None and
                           e.end_x - e.x >= 20 for e in response)
    if response and found and high_response < high_press and blue_progressive >= 5:
        evidence = tuple(e.id for e in response if e.team == BLUE and
                         e.type == "pass" and e.outcome == "complete" and
                         e.end_x is not None and e.end_x - e.x >= 20)
        found.append(Insight(
            "press_response", response[-1].second, response[-1].id, "press_response",
            {"window": "63:20–64:59", "previous_window": "61:40–63:19",
             "red_high_recoveries": high_response,
             "previous_high_recoveries": high_press,
             "blue_completed_progressive_passes": blue_progressive,
             "progressive_pass_definition": "completed pass advancing at least 20% of pitch length"},
            evidence))
    return found


EVENTS = generate_match()
INSIGHTS = detect_insights(EVENTS)
