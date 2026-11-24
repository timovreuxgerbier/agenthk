# harness/schema.py — SHARED. The only vocabulary every lane uses.
# Changes here are the architect's call (Sphinx, D17), followed by a golden-set rerun.
# A change that alters what the product does or promises goes to the team first.

from pathlib import Path

# ---- Where things live ---------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = ROOT / "screenshots"          # the ONLY folder the agent reads
SPEC = ROOT / "spec.md"                     # Pip's task + rules; the agent never edits it
ZIPPY_SPEC = ROOT / "zippy.md"              # Zippy's one question; the agent never edits it
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
# 127.0.0.1, not "localhost" (measured Nov 23): on Windows "localhost" is tried as IPv6
# first; Ollama listens on IPv4 only, so every call waited 2.05 s before falling back.
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
# Lesson 13: after each call, ask Ollama under which settings that model ran
# (context window, how much of it sits on the GPU) and Ollama's version. Numbers only.
OLLAMA_PS_URL = "http://127.0.0.1:11434/api/ps"
OLLAMA_VERSION_URL = "http://127.0.0.1:11434/api/version"
SERVER_TIMEOUT_SECONDS = 3   # a slow answer here must never slow or stop a run
CALL_TIMEOUT_SECONDS = 300

# ---- Run limits (proposal: 10 files, 15 calls, 5 minutes) -----------------
# Enforced by harness/caps.py. A run stops cleanly when any limit is reached.
# Since S8 each screenshot costs 2 calls (Zippy + Pip), so 15 calls cover ~7 files.
DEFAULT_MAX_FILES = 3
MAX_FILES_PER_RUN = 10
MAX_CALLS_PER_RUN = 15
MAX_RUN_SECONDS = 300
CONFIDENCE_FLOOR = 0.6       # below this a proposal is flagged as a guess

# ---- Zippy's answer (the sensitivity gate, D18-D21, D23) -------------------
# Multiple choice only: no free-text field exists, so Zippy cannot repeat what it saw.
# Any kind except GATE_CLEAR locks the screenshot: Pip never sees it, no rename.
# D23 (S9): the kinds are a LADDER, most harmful to expose first. When more than one
# fits, Zippy picks the highest. Order rule: how badly exposure hurts and whether it
# can be undone (a password can be changed; a licence or SSN number cannot).
GATE_CLEAR = "none"
GATE_KINDS = [
    "nudity_or_children", "government_id", "credentials", "health_record",
    "bank_or_payment", "official_document", "private_message", "contact_details",
    "marked_confidential", GATE_CLEAR,
]
GATE_SHAPE = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": GATE_KINDS},
        "confidence": {"type": "number"},
    },
    "required": ["kind", "confidence"],
}

# ---- Pip's proposal contract ---------------------------------------------
# Actions say WHERE a screenshot goes. Renaming is not an action: it happens in
# addition to keeping (team decision, Nov 10). See harness/naming.py.
ACTIONS = ["keep_image", "keep_text", "to_be_deleted", "sensitive"]
ACTIONS_THAT_KEEP = ["keep_image", "keep_text"]   # only these can be renamed
IMAGE_TYPES = [".png", ".jpg", ".jpeg"]

PROPOSAL_FIELDS = ["reason", "new_name", "why_saved_guess", "action", "confidence"]

# The JSON shape Pip must answer in. Ollama enforces it.
# Order matters: the model writes fields top to bottom, so it describes the
# image (reason) BEFORE it picks the action. new_name comes right after reason,
# so the name is drawn from the description.
PROPOSAL_SHAPE = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "new_name": {"type": "string"},
        "why_saved_guess": {"type": "string"},
        "action": {"type": "string", "enum": ACTIONS},
        "confidence": {"type": "number"},
    },
    "required": PROPOSAL_FIELDS,
}

# One trace line. Every lane that writes to the trace uses exactly these keys.
# "gate" is Zippy's verdict {"kind", "confidence"}; missing in runs before S8.
# S10: "zippy_model" and "zippy_seconds" are Zippy's own model and time (Pip's is "model").
# S11: "zippy_usage" and "pip_usage" are Ollama's own counts for each buddy's call
# (tokens read and written, load / read / write seconds). None when that buddy didn't run.
# Lesson 13: each usage also holds "context", "gpu_share" (1.0 = all on the GPU, 0 = CPU)
# and "ollama_version", asked from Ollama right after that call. None = Ollama didn't say.
# No new trace field: old runs read the same, and each buddy keeps its own settings.
# Counts only: no text, so they are safe to keep for locked screenshots too.
TRACE_FIELDS = [
    "run_id", "time", "file", "model", "zippy_model", "seconds", "zippy_seconds", "gate",
    "zippy_usage", "pip_usage",
    "raw_output", "check_problems", "flagged", "user_decision",
]
