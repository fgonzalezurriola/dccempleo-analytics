from __future__ import annotations

import unittest

from dccempleo_analytics.llm import OfferLabel


class OfferLabelTests(unittest.TestCase):
    def test_confidence_maps_text_labels(self) -> None:
        label = OfferLabel.model_validate({"confidence": "HIGH"})
        self.assertEqual(label.confidence, 0.85)

    def test_confidence_maps_percentage(self) -> None:
        label = OfferLabel.model_validate({"confidence": "80%"})
        self.assertEqual(label.confidence, 0.8)

    def test_confidence_invalid_string_falls_back_to_zero(self) -> None:
        label = OfferLabel.model_validate({"confidence": "very sure"})
        self.assertEqual(label.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
