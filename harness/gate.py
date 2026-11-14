# harness/gate.py — Zippy, the sensitivity gate (D18, D19, D20). Lane: Sphinx.
# Zippy sees every screenshot FIRST and answers one multiple-choice question: what
# kind of private thing is this, if any? There is no free-text field, so Zippy cannot
# repeat what it saw. Any kind except "none" LOCKS the screenshot: Pip never sees it,
# it is never renamed, and the trace keeps only the kind and confidence.
# A broken or missing answer locks too (fail closed): being unsure is not "clear".

import json

from harness import schema, context, router

GATE_ERROR = "gate_error"   # our code's own kind: Zippy's answer was unusable, so we lock


def read_instructions():
    """Return zippy.md as text, or None if it is missing."""
    return context.read_spec(schema.ZIPPY_SPEC)


def check_verdict(raw):
    """Turn Zippy's raw answer into {"kind", "confidence"}. Always usable: broken = locked."""
    try:
        answer = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"kind": GATE_ERROR, "confidence": None}
    if not isinstance(answer, dict) or answer.get("kind") not in schema.GATE_KINDS:
        return {"kind": GATE_ERROR, "confidence": None}
    confidence = answer.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        confidence = None
    return {"kind": answer["kind"], "confidence": confidence}


def ask(model, instructions, image_path):
    """Ask Zippy about one screenshot. Raises urllib errors or TimeoutError like router.ask."""
    messages = context.build_messages(instructions, image_path, context.ZIPPY_INSTRUCTION)
    return check_verdict(router.ask(model, messages, schema.GATE_SHAPE))


def is_locked(verdict):
    """True if Zippy ran and did NOT say "none". No verdict (runs before S8) = not locked."""
    return isinstance(verdict, dict) and verdict.get("kind") != schema.GATE_CLEAR


def is_cleared(verdict):
    """True only if Zippy ran and said "none". Renames need this (D18)."""
    return isinstance(verdict, dict) and verdict.get("kind") == schema.GATE_CLEAR
