"""Seeded fictional 10 Hz football scene built from movement priors, not match rows.

Coordinates are metres on a 105 x 68 pitch, centred at (0, 0). The sampled
SkillCorner reference is used only for broad speed and timing limits. No
tracking frame, player identity, event, or continuous path is copied.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

FPS = 10
DURATION = 70.0
SEED = 81427
PITCH_X = 52.5
PITCH_Y = 34.0


@dataclass(frozen=True)
class Player:
    id: str
    team: str
    number: int
    role: str
    x: float
    y: float

    def public(self) -> dict:
        return {"id": self.id, "team": self.team, "number": self.number,
                "role": self.role}


BLUE = [
    Player("B1", "Blue", 1, "GK", -48, 0),
    Player("B2", "Blue", 2, "RB", -28, -27),
    Player("B4", "Blue", 4, "RCB", -37, -9),
    Player("B5", "Blue", 5, "LCB", -37, 9),
    Player("B3", "Blue", 3, "LB", -28, 27),
    Player("B6", "Blue", 6, "DM", -20, 0),
    Player("B8", "Blue", 8, "RCM", -10, -15),
    Player("B10", "Blue", 10, "LCM", -10, 15),
    Player("B7", "Blue", 7, "RW", 5, -27),
    Player("B9", "Blue", 9, "ST", 10, 0),
    Player("B11", "Blue", 11, "LW", 5, 27),
]
RED = [
    Player("R1", "Red", 1, "GK", 48, 0),
    Player("R2", "Red", 2, "RB", 28, 27),
    Player("R4", "Red", 4, "RCB", 36, 9),
    Player("R5", "Red", 5, "LCB", 36, -9),
    Player("R3", "Red", 3, "LB", 28, -27),
    Player("R6", "Red", 6, "DM", 18, 0),
    Player("R8", "Red", 8, "RCM", 10, 15),
    Player("R10", "Red", 10, "LCM", 10, -15),
    Player("R7", "Red", 7, "RW", -3, 25),
    Player("R9", "Red", 9, "ST", -8, 0),
    Player("R11", "Red", 11, "LW", -3, -25),
]
ROSTER = BLUE + RED
INDEX = {p.id: i for i, p in enumerate(ROSTER)}


def _curve(t: float, points: list[tuple[float, float]]) -> float:
    if t <= points[0][0]:
        return points[0][1]
    for (ta, a), (tb, b) in zip(points, points[1:]):
        if t <= tb:
            u = (t - ta) / (tb - ta)
            u = u * u * (3 - 2 * u)
            return a + (b - a) * u
    return points[-1][1]


BLUE_PUSH = [(0, 0), (15, 12), (22, 17), (29, 0), (36, -2),
             (44, 0), (55, 4), (67, 20)]
RED_PRESS = [(0, 0), (23, 0), (29, -15), (35, -21), (40, -18),
             (45, -6), (52, -9), (63, -12)]
BALL_GUIDE_X = [(0, -48), (3, -37), (8, -28), (13, -9), (18, 6),
                (22, 18), (24, -8), (26, -36), (28, -48), (31, -37), (34, -28),
                (39, -31), (44, -48), (50, -36), (55, -20),
                (60, 8), (66, 30)]
BALL_GUIDE_Y = [(0, 0), (3, -9), (8, -25), (13, -16), (18, -24),
                (22, 0), (24, -12), (26, -9), (28, 0), (31, 10), (34, 25),
                (39, 7), (44, 0), (50, 9), (55, -3),
                (60, -23), (66, 0)]


def _target(p: Player, t: float) -> tuple[float, float]:
    guide_x = _curve(t, BALL_GUIDE_X)
    guide_y = _curve(t, BALL_GUIDE_Y)
    if p.team == "Blue":
        push = _curve(t, BLUE_PUSH)
        weight = .02 if p.role == "GK" else .45 if p.role in ("RCB", "LCB") else .72 if p.role in ("RB", "LB", "DM") else 1
        x = p.x + push * weight
        y = p.y + (guide_y - p.y) * (.04 if p.role == "GK" else .10)
        if 28 <= t <= 38 and p.role in ("LCB", "LB", "DM"):
            x -= 2.5
    else:
        press = _curve(t, RED_PRESS)
        weight = .01 if p.role == "GK" else .18 if p.role in ("RCB", "LCB") else .34 if p.role in ("RB", "LB", "DM") else .56 if p.role in ("RCM", "LCM") else 1
        x = p.x + press * weight
        y = p.y + (guide_y - p.y) * (.03 if p.role == "GK" else .08)
        if 27 <= t <= 38 and p.id == "R7":
            x = .10 * x + .90 * (guide_x - 1)
            y = .15 * y + .85 * (guide_y + 10)
        if 27 <= t <= 36 and p.id == "R9":
            x = .10 * x + .90 * (guide_x - 4)
            y = .25 * y + .75 * (guide_y - 5)
        if 48 <= t <= 54 and p.id == "R9":
            y = guide_y - 9
    return max(-50, min(50, x)), max(-31, min(31, y))


def generate_tracking() -> list[list]:
    """Integrate 22 independent velocity states toward a coordinated shape.

    A 6.7 m/s cap approximates the 99th percentile of one-second displacement
    in the examined reference slice. The 0.1-second ticks match its 10 Hz
    cadence. Smooth acceleration and persistent velocity prevent stop/start
    jumps at pass receptions.
    """
    rng = random.Random(SEED)
    positions = [[p.x, p.y] for p in ROSTER]
    velocities = [[rng.uniform(-.4, .4), rng.uniform(-.4, .4)] for _ in ROSTER]
    roaming = [[0.0, 0.0] for _ in ROSTER]
    next_move = [rng.uniform(.3, 2.0) for _ in ROSTER]
    frames: list[list] = []
    dt = 1 / FPS
    for tick in range(round(DURATION * FPS) + 1):
        t = tick * dt
        frame = [round(t, 1)]
        for i, p in enumerate(ROSTER):
            x, y = positions[i]
            vx, vy = velocities[i]
            tx, ty = _target(p, t)
            # Players make independent short support runs. Targets persist for
            # several seconds; they do not reset when a teammate gets the ball.
            if t >= next_move[i]:
                scale = 1.0 if p.role == "GK" else 5.0 if p.role in ("RCB", "LCB") else 10.5
                roaming[i] = [rng.uniform(-scale, scale), rng.uniform(-scale, scale)]
                next_move[i] = t + rng.uniform(3.0, 5.6)
            run_weight = .2 if (27 <= t <= 38 and p.id in ("R7", "R9", "B3", "B5")) else 1
            tx += roaming[i][0] * run_weight
            ty += roaming[i][1] * run_weight
            preferred_vx = max(-5.5, min(5.5, (tx - x) / 1.5))
            preferred_vy = max(-5.5, min(5.5, (ty - y) / 1.5))
            ax = max(-3.2, min(3.2, (preferred_vx - vx) / .65))
            ay = max(-3.2, min(3.2, (preferred_vy - vy) / .65))
            vx += ax * dt
            vy += ay * dt
            cap = 2.6 if p.role == "GK" else 6.7
            speed = math.hypot(vx, vy)
            if speed > cap:
                vx *= cap / speed
                vy *= cap / speed
            x = max(-50.5, min(50.5, x + vx * dt))
            y = max(-31.5, min(31.5, y + vy * dt))
            positions[i] = [x, y]
            velocities[i] = [vx, vy]
            frame.append([round(x, 2), round(y, 2)])
        frames.append(frame)
    return frames


TRACKING = generate_tracking()


def at(player_id: str, t: float) -> tuple[float, float]:
    point = TRACKING[round(t * FPS)][INDEX[player_id] + 1]
    return point[0], point[1]


# A new fictional sequence. Pass destinations come from the receiving player's
# generated position at arrival; no old event script or real match row is used.
ACTION_PLAN = [
    (0.8, "pass", "B1", "B4", 1.4, "complete"),
    (4.2, "pass", "B4", "B2", 1.6, "complete"),
    (8.9, "pass", "B2", "B8", 1.5, "complete"),
    (13.2, "pass", "B8", "B7", 1.7, "complete"),
    (18.7, "pass", "B7", "B9", 1.5, "complete"),
    (22.0, "pass", "B9", "B8", 1.3, "complete"),
    (24.2, "pass", "B8", "B4", 1.3, "complete"),
    (26.4, "pass", "B4", "B1", 1.1, "complete"),
    (28.2, "pass", "B1", "B5", 1.4, "complete"),
    (32.2, "pressure", "R9", "B5", 1.4, "engaged"),
    (32.8, "pass", "B5", "B3", 1.5, "complete"),
    (34.5, "pressure", "R7", "B3", 1.2, "engaged"),
    (35.0, "pass", "B3", "B6", 1.1, "intercepted"),
    (36.1, "recovery", "R7", None, .4, "won"),
    (37.2, "pass", "R7", "R9", 1.4, "complete"),
    (40.2, "shot", "R9", None, .8, "saved"),
    (44.7, "pass", "B1", "B5", 1.5, "complete"),
    (48.7, "pass", "B5", "B6", 1.5, "complete"),
    (52.4, "pressure", "R9", "B6", 1.4, "engaged"),
    (53.1, "pass", "B6", "B2", 1.7, "complete"),
    (57.1, "pass", "B2", "B7", 2.4, "complete"),
    (61.0, "pass", "B7", "B9", 1.6, "complete"),
    (66.1, "shot", "B9", None, .8, "off_target"),
]


def generate_events() -> list[dict]:
    events = []
    for i, (t, kind, actor, target, duration, outcome) in enumerate(sorted(ACTION_PLAN), 1):
        x, y = at(actor, t)
        if kind == "shot":
            end = [52.5 if actor.startswith("B") else -52.5, y * .35]
        elif kind == "pass" and outcome == "intercepted":
            end = list(at("R7", t + duration))
        elif kind == "pass":
            end = list(at(target, t + duration))
        else:
            end = None
        events.append({"id": f"S{i:03}", "t": t, "type": kind,
                       "team": "Blue" if actor.startswith("B") else "Red",
                       "actor": actor, "target": target,
                       "x": x, "y": y, "end": end,
                       "duration": duration, "outcome": outcome})
    return events


EVENTS = generate_events()


def public_scene() -> dict:
    return {"fps": FPS, "duration": DURATION, "clock_start": 31 * 60 + 20,
            "pitch": {"length": 105, "width": 68},
            "roster": [p.public() for p in ROSTER],
            "frames": TRACKING, "events": EVENTS,
            "label": "Fictional 10 Hz tactical visualization"}
