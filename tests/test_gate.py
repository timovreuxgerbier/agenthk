# tests/test_gate.py — Lane: Sphinx. Zippy's three promises, no model needed:
#   python3 -m unittest tests.test_gate
# 1. A broken answer locks (fail closed).  2. No rename without Zippy's "none" (D18).
# 3. Anything judged sensitive is stored without its description (trace redaction).

import json
import unittest

from harness import gate, naming, trace


class TestVerdict(unittest.TestCase):
    def test_good_answer_is_kept(self):
        verdict = gate.check_verdict('{"kind": "bank_or_payment", "confidence": 0.9}')
        self.assertEqual(verdict, {"kind": "bank_or_payment", "confidence": 0.9})
        self.assertTrue(gate.is_locked(verdict))

    def test_broken_answers_lock(self):
        for raw in ["not json", None, "[]", '{"kind": "sofa"}', '{"confidence": 1}']:
            verdict = gate.check_verdict(raw)
            self.assertEqual(verdict["kind"], gate.GATE_ERROR, raw)
            self.assertTrue(gate.is_locked(verdict), raw)
            self.assertFalse(gate.is_cleared(verdict), raw)

    def test_no_verdict_is_neither(self):
        # Runs from before Zippy existed: not locked, but not cleared either.
        self.assertFalse(gate.is_locked(None))
        self.assertFalse(gate.is_cleared(None))


class TestGatedRename(unittest.TestCase):
    proposal = {"action": "keep_text", "new_name": "sofia marin contact details"}

    def test_renamed_only_after_zippy_says_none(self):
        clear = {"kind": "none", "confidence": 0.9}
        self.assertEqual(naming.gated_rename(self.proposal, "IMG_1.png", clear),
                         "sofia-marin-contact-details")

    def test_no_rename_when_locked_missing_or_broken(self):
        for verdict in [{"kind": "contact_details", "confidence": 0.8}, None,
                        {"kind": gate.GATE_ERROR, "confidence": None}]:
            self.assertEqual(naming.gated_rename(self.proposal, "IMG_1.png", verdict), "",
                             verdict)


class TestRedaction(unittest.TestCase):
    pip_answer = json.dumps({"reason": "A Chase balance for Sofia Marin, $4,312.07",
                             "new_name": "sofia-chase-balance", "why_saved_guess": "x",
                             "action": "sensitive", "confidence": 0.7})

    def test_pip_sensitive_keeps_only_action_and_confidence(self):
        entry = {"gate": {"kind": "none", "confidence": 0.9}, "raw_output": self.pip_answer}
        stored = json.loads(trace.redact(entry)["raw_output"])
        self.assertEqual(stored, {"action": "sensitive", "confidence": 0.7})

    def test_zippy_lock_is_redacted_even_if_raw_has_text(self):
        entry = {"gate": {"kind": "bank_or_payment", "confidence": 0.9},
                 "raw_output": self.pip_answer.replace('"sensitive"', '"keep_text"')}
        self.assertNotIn("Sofia", trace.redact(entry)["raw_output"])

    def test_ordinary_screenshot_is_stored_as_is(self):
        raw = json.dumps({"reason": "A pasta recipe", "action": "keep_text", "confidence": 1})
        entry = {"gate": {"kind": "none", "confidence": 1.0}, "raw_output": raw}
        self.assertEqual(trace.redact(entry)["raw_output"], raw)


if __name__ == "__main__":
    unittest.main()
