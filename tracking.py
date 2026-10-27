"""Synthetic 11v11 positions constrained by the event stream.

This is a tactical illustration, not measured player tracking. Event actors and
successful pass recipients have fixed positions at event time. Everyone else
occupies a 4-3-3 shape that shifts with play. Positions are interpolated
between anchors without teleporting.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from math import exp, hypot

from engine import BLUE, RED, EVENTS, Event


@dataclass(frozen=True)
class Player:
    team: str
    name: str
    number: int
    role: str
    x: float
    y: float

    def public(self) -> dict:
        return {"team": self.team, "name": self.name,
                "number": self.number, "role": self.role}


def _team(team: str, names: list[tuple[str, int, str, float, float]]) -> list[Player]:
    return [Player(team, name, number, role, x if team == BLUE else 100 - x, y)
            for name, number, role, x, y in names]


ROSTER = _team(BLUE, [
    ("B. Vale", 1, "GK", 7, 50),
    ("F. Torres", 2, "RB", 25, 18),
    ("M. Chen", 4, "RCB", 22, 40),
    ("I. Malik", 5, "LCB", 22, 60),
    ("N. Bell", 3, "LB", 25, 82),
    ("A. Noor", 6, "DM", 39, 50),
    ("K. Adeyemi", 8, "RCM", 48, 30),
    ("P. Singh", 10, "LCM", 48, 70),
    ("D. Park", 7, "RW", 72, 20),
    ("S. Costa", 9, "ST", 78, 50),
    ("E. Hart", 11, "LW", 72, 80),
]) + _team(RED, [
    ("L. Reed", 1, "GK", 7, 50),
    ("C. Bell", 2, "RB", 25, 18),
    ("M. Diallo", 4, "RCB", 22, 40),
    ("G. Ward", 5, "LCB", 22, 60),
    ("A. Patel", 3, "LB", 25, 82),
    ("J. Kim", 6, "DM", 39, 50),
    ("N. Cruz", 8, "RCM", 48, 30),
    ("O. Brooks", 10, "LCM", 48, 70),
    ("R. Silva", 7, "RW", 72, 20),
    ("T. Okafor", 9, "ST", 78, 50),
    ("V. Mensah", 11, "LW", 72, 80),
])


def _flight(e: Event) -> float:
    distance = hypot((e.end_x - e.x) * 1.05, (e.end_y - e.y) * .68)
    if e.type == "shot":
        return min(1.2, max(.5, distance / 30))
    return min(2.4, max(.9, distance / 12))


def _ball_at(events: list[Event], index: int, t: float) -> tuple[float, float]:
    e = events[index]
    if e.type in ("pass", "shot") and e.end_x is not None:
        f = min(1, max(0, (t - e.second) / _flight(e)))
        return (e.x + (e.end_x - e.x) * f,
                e.y + (e.end_y - e.y) * f)
    if e.type in ("pressure", "tackle"):
        for prior in reversed(events[:index]):
            if prior.possession_id != e.possession_id:
                break
            if prior.type == "pass" and prior.outcome == "complete":
                return prior.end_x, prior.end_y
    return e.x, e.y


def _anchors(events: list[Event]) -> dict[str, list[tuple[float, float, float]]]:
    result: dict[str, list[tuple[float, float, float]]] = {p.name: [] for p in ROSTER}
    for e in events:
        if e.type != "possession_change":
            result[e.player].append((float(e.second), float(e.x), float(e.y)))
        if e.type == "pass" and e.outcome == "complete" and e.recipient:
            result[e.recipient].append((e.second + _flight(e), float(e.end_x), float(e.end_y)))
    for points in result.values():
        points.sort()
    return result


def _mix(a: tuple[float, float], b: tuple[float, float], weight: float) -> tuple[float, float]:
    return (a[0] * (1 - weight) + b[0] * weight,
            a[1] * (1 - weight) + b[1] * weight)


def _smooth(value: float) -> float:
    f = min(1, max(0, value))
    return f * f * (3 - 2 * f)


def _support_offset(player: Player, ball_x: float,
                    in_possession: bool) -> float:
    """Move a few metres toward the ball while retaining each positional line."""
    if player.role == "GK":
        return 0.0
    line = ("front" if player.role in ("RW", "ST", "LW") else
            "mid" if player.role in ("DM", "RCM", "LCM") else "back")
    rate = {"front": .09, "mid": .07, "back": .04}[line]
    if not in_possession:
        rate *= 1.1 if line == "front" else .6
    return max(-4, min(4, (ball_x - player.x) * rate))


def _position(player: Player, points: list[tuple[float, float, float]],
              t: float, shift_x: float, shift_y: float) -> tuple[float, float]:
    factor = {"GK": .08, "RB": .55, "RCB": .5, "LCB": .5, "LB": .55,
              "DM": .8, "RCM": .9, "LCM": .9, "RW": 1, "ST": 1, "LW": 1}[player.role]
    base = (player.x + shift_x * factor, player.y + shift_y * factor)
    if not points:
        return base
    times = [point[0] for point in points]
    index = bisect_left(times, t)
    if index < len(points) and points[index][0] == t:
        return points[index][1], points[index][2]
    if index == 0:
        anchor = points[0]
        weight = _smooth(1 - (anchor[0] - t) / 18)
        return _mix(base, anchor[1:], weight)
    if index == len(points):
        anchor = points[-1]
        weight = _smooth(1 - (t - anchor[0]) / 18)
        return _mix(base, anchor[1:], weight)
    a, b = points[index - 1], points[index]
    gap = b[0] - a[0]
    if gap <= 20:
        return _mix(a[1:], b[1:], (t - a[0]) / gap)
    transition = min(18, gap / 3)
    if t - a[0] < transition:
        return _mix(a[1:], base, _smooth((t - a[0]) / transition))
    if b[0] - t < transition:
        return _mix(base, b[1:], _smooth(1 - (b[0] - t) / transition))
    return base


def generate_tracking(events: list[Event] = EVENTS) -> dict:
    anchors = _anchors(events)
    anchor_times = {t for points in anchors.values() for t, _, _ in points}
    times = {events[0].second + i * .5 for i in range(
        int((events[-1].second + 3 - events[0].second) * 2) + 1)
        if all(abs(events[0].second + i * .5 - anchor) >= .1
               for anchor in anchor_times)}
    times.update(anchor_times)
    ordered_times = sorted(times)
    frames: list[list] = []
    event_index = 0
    shape: dict[str, tuple[float, float]] = {}
    previous_t = ordered_times[0]
    for t in ordered_times:
        while event_index + 1 < len(events) and events[event_index + 1].second <= t:
            event_index += 1
        possession = events[event_index].possession_id
        controlling_team = BLUE if possession.startswith("B") else RED
        ball_x, ball_y = _ball_at(events, event_index, t)
        wanted_x = max(-13, min(13, (ball_x - 50) * .30))
        wanted_y = max(-7, min(7, (ball_y - 50) * .18))
        dt = t - previous_t
        positions = []
        for player in ROSTER:
            lateral = max(-3, min(3, (ball_y - player.y) * .06))
            target = (wanted_x + _support_offset(player, ball_x,
                                                 player.team == controlling_team),
                      wanted_y + lateral)
            if player.name not in shape:
                shape[player.name] = target
            else:
                x, y = shape[player.name]
                tau = 2.8 + player.number % 5 * .8
                if player.role == "GK":
                    tau += 2
                alpha = 1 - exp(-dt / tau)
                shape[player.name] = (x + (target[0] - x) * alpha,
                                      y + (target[1] - y) * alpha)
            x, y = _position(player, anchors[player.name], t, *shape[player.name])
            positions.append((x, y))
        frames.append([round(t, 3)] + [[round(x, 2), round(y, 2)]
                                          for x, y in positions])
        previous_t = t
    return {"roster": [player.public() for player in ROSTER], "frames": frames}


TRACKING = generate_tracking()
