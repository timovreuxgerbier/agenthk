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

## What stage 1 does and doesn't do

- **Only looks.** It installs, downloads, runs, moves and deletes nothing. No team code changes:
  it reads `shyft_requirements.json` and asks Ollama the same questions the cloud lock asks.
- Still a terminal window (stage 4 removes it). Getting what's missing is stage 2.

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
| `test_shyft_app.py` | 21 tests: the safety rules (including a cross-site page), the status answer, the review, and D38 (app/ changes no files and builds no personal path). |
| `../ui/live.js` | The screens' side: notices the server and asks it, with the key. |

Tests: `python3 -m unittest app.test_shyft_app`

## Not checked yet on a real Windows PC

Installed memory through Windows' own call (GetPhysicallyInstalledSystemMemory), the graphics card question (asked with no window), and whether
antivirus reacts to a program listening on 127.0.0.1.
