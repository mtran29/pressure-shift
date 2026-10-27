import unittest

from engine import EVENTS, INSIGHTS, detect_insights, generate_match
from foundry import fallback


class MatchTests(unittest.TestCase):
    def test_deterministic_and_unique(self):
        self.assertEqual(EVENTS, generate_match())
        self.assertEqual(len(EVENTS), len({e.id for e in EVENTS}))

    def test_two_grounded_shifts(self):
        self.assertEqual([i.kind for i in INSIGHTS], ["pressure_surge", "press_response"])
        self.assertEqual(INSIGHTS[0].facts["red_attacking_third_pressures"], 6)
        self.assertEqual(INSIGHTS[0].facts["red_high_recoveries"], 2)
        self.assertEqual(INSIGHTS[1].facts["blue_completed_progressive_passes"], 5)
        event_ids = {e.id for e in EVENTS}
        for insight in INSIGHTS:
            self.assertTrue(insight.evidence_ids)
            self.assertTrue(set(insight.evidence_ids) <= event_ids)

    def test_no_pressure_no_story(self):
        without_red = [e for e in EVENTS if e.team != "Red FC"]
        self.assertEqual(detect_insights(without_red), [])

    def test_passes_connect_within_each_possession(self):
        for possession_id in {e.possession_id for e in EVENTS}:
            passes = [e for e in EVENTS if e.possession_id == possession_id
                      and e.type == "pass"]
            for previous, following in zip(passes, passes[1:]):
                self.assertEqual(previous.outcome, "complete")
                self.assertEqual((previous.end_x, previous.end_y),
                                 (following.x, following.y))
                self.assertLessEqual(following.second - previous.second, 10)
                self.assertEqual(previous.recipient, following.player)

    def test_high_press_is_in_blue_defensive_third(self):
        press = [e for e in EVENTS if e.phase == "press" and e.team == "Red FC"
                 and e.type in ("pressure", "recovery")]
        self.assertTrue(press)
        self.assertTrue(all(e.x <= 33 for e in press))
        self.assertEqual(EVENTS, sorted(EVENTS, key=lambda e: (e.second, e.id)))

    def test_fallback_is_labeled(self):
        for insight in INSIGHTS:
            item = fallback(insight, "test")
            self.assertIn("fallback", item["source"].lower())
            self.assertLessEqual(len(item["overlay"].split()), 18)


if __name__ == "__main__":
    unittest.main()
