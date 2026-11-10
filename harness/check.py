# harness/check.py — Lane: Timo (after the model)
# Our code, not the model, decides whether a proposal is allowed through.
# Later: check that any destination path stays inside the agent's folders.

import json

from harness import schema


def check_proposal(raw):
    """Return (proposal_or_None, list_of_problems)."""
    try:
        proposal = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, ["not valid JSON"]
    if not isinstance(proposal, dict):
        return None, ["not a JSON object"]

    problems = []
    if proposal.get("action") not in schema.ACTIONS:
        problems.append("action not allowed")
    confidence = proposal.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        problems.append("confidence missing or not between 0 and 1")
    if proposal.get("action") == "rename" and not proposal.get("new_name"):
        problems.append("rename proposed without a new name")
    return proposal, problems


def is_flagged(proposal, problems):
    """A proposal is flagged for review if it failed a check or the model was unsure."""
    if problems or proposal is None:
        return True
    confidence = proposal.get("confidence", 0)
    return not isinstance(confidence, (int, float)) or confidence < schema.CONFIDENCE_FLOOR
