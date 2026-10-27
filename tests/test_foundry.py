import json
import unittest
from unittest.mock import patch

from engine import INSIGHTS
from foundry import narrate


class FoundryTests(unittest.TestCase):
    @patch("foundry.configured", return_value=True)
    @patch("foundry._request")
    def test_rejects_unknown_evidence(self, request, _configured):
        request.return_value = {"choices": [{"message": {"content": json.dumps({
            "overlay": "A grounded overlay", "casual": "Casual wording",
            "analyst": "Analyst wording", "evidence_ids": ["E999"]
        })}}]}
        result = narrate(INSIGHTS[0])
        self.assertIn("fallback", result["source"].lower())

    @patch("foundry.configured", return_value=True)
    @patch("foundry._request")
    def test_accepts_grounded_evidence(self, request, _configured):
        request.return_value = {"choices": [{"message": {"content": json.dumps({
            "overlay": "Red's high recoveries have risen.",
            "casual": "Red is winning the ball near Blue's goal more often.",
            "analyst": "Three high recoveries followed none in the preceding window.",
            "evidence_ids": [INSIGHTS[0].evidence_ids[0]]
        })}}], "usage": {"total_tokens": 100}}
        result = narrate(INSIGHTS[0])
        self.assertIn("Foundry", result["source"])
        self.assertEqual(result["usage"]["total_tokens"], 100)


if __name__ == "__main__":
    unittest.main()
