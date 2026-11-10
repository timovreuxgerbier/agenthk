# harness/schema.py — SHARED. The only vocabulary every lane uses.
# Changing anything here is a TEAM decision, followed by a golden-set rerun.

from pathlib import Path

# ---- Where things live ---------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = ROOT / "screenshots"          # the ONLY folder the agent reads
SPEC = ROOT / "spec.md"                     # task + rules; the agent never edits it
TRACE = ROOT / "trace.jsonl"                # one line per screenshot per run
GOLDEN = ROOT / "golden" / "golden.csv"     # your labels; outside the read folder
SCORE_REPORT = ROOT / "golden" / "score_report.txt"

# Output folders (created by execute.py later; listed here so nobody invents names)
OUTPUT_FOLDERS = {
    "keep_image": ROOT / "Retained as Images",
    "keep_text": ROOT / "Retained as Text",
    "to_be_deleted": ROOT / "To Be Deleted",
    "sensitive": ROOT / "Sensitive - For Human Review",
}

# ---- Model settings ------------------------------------------------------
DEFAULT_MODEL = "gemma4:e4b"
OLLAMA_URL = "http://localhost:11434/api/chat"
CALL_TIMEOUT_SECONDS = 300

# ---- Run limits (proposal: 10 files, 15 calls, 5 minutes) -----------------
# Enforced by harness/caps.py. A run stops cleanly when any limit is reached.
DEFAULT_MAX_FILES = 3
MAX_FILES_PER_RUN = 10
MAX_CALLS_PER_RUN = 15
MAX_RUN_SECONDS = 300
CONFIDENCE_FLOOR = 0.6       # below this a proposal is flagged as a guess

# ---- The proposal contract -----------------------------------------------
ACTIONS = ["keep_image", "keep_text", "rename", "to_be_deleted", "sensitive"]
IMAGE_TYPES = [".png", ".jpg", ".jpeg"]

PROPOSAL_FIELDS = ["reason", "why_saved_guess", "action", "new_name", "confidence"]

# The JSON shape the model must answer in. Ollama enforces it.
# Order matters: the model writes fields top to bottom, so it describes the
# image (reason) BEFORE it picks the action. Nov 10 runs: with action first it
# wrote "a school report card with grades" and still chose keep_image.
PROPOSAL_SHAPE = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "why_saved_guess": {"type": "string"},
        "action": {"type": "string", "enum": ACTIONS},
        "new_name": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": PROPOSAL_FIELDS,
}

# One trace line. Every lane that writes to the trace uses exactly these keys.
TRACE_FIELDS = [
    "run_id", "time", "file", "model", "seconds",
    "raw_output", "check_problems", "flagged", "user_decision",
]
