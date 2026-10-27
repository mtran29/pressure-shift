import math
import unittest

from foundry import fallback, validate
from insights import CANDIDATES
from simulation import DURATION, EVENTS, FPS, ROSTER, TRACKING, at, generate_tracking


class SceneTests(unittest.TestCase):
    def test_tracking_cadence_and_physical_bounds(self):
        self.assertEqual(len(ROSTER), 22)
        self.assertEqual(len(TRACKING), round(DURATION * FPS) + 1)
        self.assertEqual(TRACKING, generate_tracking())
        speeds = []
        for a, b in zip(TRACKING, TRACKING[1:]):
            self.assertAlmostEqual(b[0] - a[0], .1)
            for p, q in zip(a[1:], b[1:]):
                self.assertTrue(-52.5 <= q[0] <= 52.5)
                self.assertTrue(-34 <= q[1] <= 34)
                speeds.append(math.dist(p, q) * FPS)
        self.assertLessEqual(max(speeds), 6.85)
        self.assertGreater(sorted(speeds)[len(speeds)//2], 1.3)
        one_second = sorted(math.dist(p, q)
                            for a, b in zip(TRACKING, TRACKING[10:])
                            for p, q in zip(a[1:], b[1:]))
        self.assertTrue(1.3 < one_second[len(one_second)//2] < 2.5)
        self.assertTrue(3.5 < one_second[int(.9*len(one_second))] < 5.8)

    def test_pressure_is_a_close_challenge_after_reception(self):
        for e in EVENTS:
            if e["type"] != "pressure":
                continue
            self.assertLessEqual(math.dist(at(e["actor"], e["t"]),
                                           at(e["target"], e["t"])), 6.1)
        pressured = next(e for e in EVENTS if e["t"] == 34.5)
        previous_pass = next(e for e in EVENTS if e["t"] == 32.8)
        self.assertGreaterEqual(pressured["t"], previous_pass["t"] + previous_pass["duration"])

    def test_ball_actions_form_one_continuous_possession_story(self):
        self.assertEqual(EVENTS, sorted(EVENTS, key=lambda e: e["t"]))
        owner = "B1"
        for e in EVENTS:
            if e["type"] == "pressure":
                continue
            if e["type"] == "recovery":
                self.assertEqual(e["actor"], "R7")
                owner = e["actor"]
                continue
            self.assertEqual(e["actor"], owner, e["id"])
            if e["type"] == "pass":
                owner = "R7" if e["outcome"] == "intercepted" else e["target"]
            elif e["type"] == "shot":
                owner = "B1" if e["team"] == "Red" else "R1"

    def test_insights_are_triggered_after_evidence(self):
        self.assertEqual([x["kind"] for x in CANDIDATES], ["pressure_turn", "blue_escape"])
        by_id = {e["id"]: e for e in EVENTS}
        for candidate in CANDIDATES:
            self.assertGreaterEqual(candidate["trigger_t"],
                                    max(by_id[id]["t"] for id in candidate["evidence_ids"]))
            self.assertTrue(set(candidate["evidence_ids"]) <= by_id.keys())

    def test_foundry_editorial_is_grounded(self):
        for candidate in CANDIDATES:
            local = fallback(candidate)
            self.assertEqual(validate(candidate, local)["focus_event_id"],
                             candidate["focus_event_id"])
            bad = {**local, "evidence_ids": ["NOT_AN_EVENT"]}
            with self.assertRaises(ValueError):
                validate(candidate, bad)


if __name__ == "__main__":
    unittest.main()
