# app/ — Shyft's screens with real answers (Lane: Ana)

Stage 1 of the Windows app plan ("Shyft for Windows - app plan for Sphinx"). Proposal for review.

## Run it

```
python3 app/shyft_app.py
```

(One Python for the team: python3. On a Windows PC where only `py` or `python` works, use that.)

It opens Shyft's screens in your browser. **Get started** shows the Spec screen with the numbers
from `shyft_requirements.json` and what this computer has; **Continue** shows Setup 1 with the real
state of Ollama and of both model files, checked by id (D27). Close the window or press Ctrl+C to stop.

Opened as a plain file (`ui/index.html`), the screens are the prototype again, as before.

## What stages 1 and 2 do and don't do

- **Stage 1 looks.** It reads `shyft_requirements.json` and asks Ollama the same questions the cloud lock asks.
- **Stage 2 does two jobs, one at a time** (`jobs.py`), each with a Stop button; closing the window stops them too:
  - **Get what's missing:** downloads a missing model through Ollama's own `/api/pull`, with progress.
    A model that is there but a different build is **never replaced** (it's someone's own model): the screen says so.
    Ollama itself the person still installs.
  - **Sort:** starts the team's `run.py RICK all --zippy ZIPPY` (the two long names, D27), on the
    made-up test set only. It refuses, in plain words, if that set isn't loaded, a model is missing, or the cloud is on.
    Progress comes from run.py's own lines (`[n/N] ... Zippy is looking`, `Took`), and the where-notice
    is shown as run.py prints it. **File names never reach the screens.**
- **Nothing is moved, renamed or deleted:** run.py only proposes. It writes its own `trace.jsonl`, as always.
- The review of a real run is stage 3 (run.py writes the trace, not a review file), so "Done" says that
  instead of showing an old review. Still a terminal window (stage 4 removes it).

## Safety (plan, section 6; D38)

- 127.0.0.1 only, a random port each time.
- A secret key in the address; every `/api/` request needs it (`X-Shyft-Key`).
- The Host header must be that exact address (no DNS rebinding).
- Other websites get nothing, files included: a request whose `Sec-Fetch-Site` is anything but
  `same-origin` or `none` is refused, and a POST must carry our own Origin.
- A strict Content-Security-Policy: only our own script files run (no inline script), nothing loads
  from elsewhere. Inline *styles* are allowed: progress bars and buddy sizes use them, and styles
  can't run code.
- Serves only Shyft's screens from `ui/`, read-only, never `review_data.js` (the made-up demo, for
  the page opened as a file). Real reviews come only through the keyed `/api/review`.
- Builds no path to a person's files or the home: the newest review is found by
  `harness/records.py` (stage 0.3). Before 0.3, `/api/review` answers "No review yet."
- Talks to nothing but Ollama on this computer.

## Files

| File | What it does |
|---|---|
| `shyft_app.py` | The server and its safety rules. `/api/status`, `/api/review`, `/api/quit`. |
| `checks.py` | What is true on this computer: memory, free disk, graphics, Ollama, model ids. |
| `jobs.py` | Stage 2: the two jobs (download, sort), one at a time, and Stop. |
| `test_jobs.py` | 15 tests: models under their short names (nothing to download; run.py gets the names they are under), progress from run.py's lines, no file names on screen, one job at a time, Stop and Quit, the refusals, downloads only what's missing, never replaces a different build, key and Origin on the new endpoints. |
| `../ui/live_jobs.js` | The screens' side of the jobs: Setup 1's download and the sorting screen. |
| `test_shyft_app.py` | 21 tests: the safety rules (including a cross-site page), the status answer, the review, and D38 (app/ changes no files and builds no personal path). |
| `../ui/live.js` | The screens' side: notices the server and asks it, with the key. |

Tests: `python3 -m unittest app.test_shyft_app app.test_jobs`

## Not checked yet on a real Windows PC

Installed memory through Windows' own call (GetPhysicallyInstalledSystemMemory), the graphics card question (asked with no window), and whether
antivirus reacts to a program listening on 127.0.0.1. Stage 2: a real 4.6 to 6.6 GB download through Ollama,
and a real run.py on the made-up set (checked here only with stand-ins that print run.py's own lines).
