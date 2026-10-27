import unittest

from engine import EVENTS, INSIGHTS, detect_insights, generate_match
from foundry import fallback


class MatchTests(unittest.TestCase):
    def test_deterministic_and_unique(self):
        self.assertEqual(EVENTS, generate_match())
        self.assertEqual(len(EVENTS), len({e.id for e in EVENTS}))

    def test_two_grounded_shifts(self):
        self.assertEqual([i.kind for i in INSIGHTS], ["pressure_surge", "press_response"])
        event_ids = {e.id for e in EVENTS}
        for insight in INSIGHTS:
            self.assertTrue(insight.evidence_ids)
            self.assertTrue(set(insight.evidence_ids) <= event_ids)

    def test_no_pressure_no_story(self):
        without_red = [e for e in EVENTS if e.team != "Red FC"]
        self.assertEqual(detect_insights(without_red), [])

    def test_fallback_is_labeled(self):
        for insight in INSIGHTS:
            item = fallback(insight, "test")
            self.assertIn("fallback", item["source"].lower())
            self.assertLessEqual(len(item["overlay"].split()), 18)


if __name__ == "__main__":
    unittest.main()

