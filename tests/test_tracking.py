import math
import unittest

from engine import EVENTS
from tracking import ROSTER, TRACKING, _flight


class TrackingTests(unittest.TestCase):
    def test_full_sides_and_shape(self):
        for team in ("Blue FC", "Red FC"):
            side = [player for player in ROSTER if player.team == team]
            self.assertEqual(len(side), 11)
            self.assertEqual(len({player.number for player in side}), 11)
            self.assertEqual(sum(p.role == "GK" for p in side), 1)
            self.assertEqual(sum(p.role in ("RB", "RCB", "LCB", "LB") for p in side), 4)
            self.assertEqual(sum(p.role in ("DM", "RCM", "LCM") for p in side), 3)
            self.assertEqual(sum(p.role in ("RW", "ST", "LW") for p in side), 3)

    def test_event_actors_arrive_at_event_positions(self):
        by_time = {frame[0]: frame for frame in TRACKING["frames"]}
        by_name = {player.name: index + 1 for index, player in enumerate(ROSTER)}
        for event in EVENTS:
            if event.type == "possession_change":
                continue
            position = by_time[event.second][by_name[event.player]]
            self.assertLessEqual(abs(position[0] - event.x), .01, event.id)
            self.assertLessEqual(abs(position[1] - event.y), .01, event.id)

    def test_positions_and_speeds_remain_plausible(self):
        frames = TRACKING["frames"]
        self.assertTrue(frames)
        for frame in frames:
            self.assertEqual(len(frame), 23)
            for x, y in frame[1:]:
                self.assertTrue(0 <= x <= 100 and 0 <= y <= 100)
        for before, after in zip(frames, frames[1:]):
            dt = after[0] - before[0]
            self.assertGreater(dt, 0)
            for a, b in zip(before[1:], after[1:]):
                metres = math.hypot((b[0] - a[0]) * 1.05,
                                    (b[1] - a[1]) * .68)
                self.assertLessEqual(metres / dt, 9.5)

    def test_completed_pass_recipients_meet_the_ball(self):
        by_time = {frame[0]: frame for frame in TRACKING["frames"]}
        by_name = {player.name: index + 1 for index, player in enumerate(ROSTER)}
        for event in EVENTS:
            if event.type != "pass" or event.outcome != "complete":
                continue
            arrival = round(event.second + _flight(event), 3)
            position = by_time[arrival][by_name[event.recipient]]
            self.assertLessEqual(abs(position[0] - event.end_x), .02, event.id)
            self.assertLessEqual(abs(position[1] - event.end_y), .02, event.id)


if __name__ == "__main__":
    unittest.main()
