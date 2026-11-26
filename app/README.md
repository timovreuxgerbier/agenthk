# app/ — Shyft's screens with real answers (Lane: Ana)

Stage 1 of the Windows app plan ("Shyft for Windows - app plan for Sphinx"). Proposal for review.

## Run it

```
python app/shyft_app.py          (Mac: python3 app/shyft_app.py)
```

It opens Shyft's screens in your browser. **Get started** shows the Spec screen with the numbers
from `shyft_requirements.json` and what this computer has; **Continue** shows Setup 1 with the real
state of Ollama and of both model files, checked by id (D27). Close the window or press Ctrl+C to stop.

Opened as a plain file (`ui/index.html`), the screens are the prototype again, as before.

## What stage 1 does and doesn't do

- **Only looks.** It installs, downloads, runs, moves and deletes nothing. No team code changes:
  it reads `shyft_requirements.json` and asks Ollama the same questions the cloud lock asks.
- Still a terminal window (stage 4 removes it). Getting what's missing is stage 2.

## Safety (plan, section 6)

- 127.0.0.1 only, a random port each time.
- A secret key in the address; every `/api/` request needs it (`X-Shyft-Key`).
- The Host header must be that exact address (no DNS rebinding).
- Serves only files inside `ui/`, read-only; never takes a path from the browser.
- Talks to nothing but Ollama on this computer.

## Files

| File | What it does |
|---|---|
| `shyft_app.py` | The server and its safety rules. `/api/status`, `/api/quit`. |
| `checks.py` | What is true on this computer: memory, free disk, graphics, Ollama, model ids. |
| `test_shyft_app.py` | 12 tests: the safety rules and the status answer, with a stand-in Ollama. |
| `../ui/live.js` | The screens' side: notices the server and asks it, with the key. |

Tests: `python -m unittest app.test_shyft_app`

## Not checked yet on a real Windows PC

Memory through Windows' own call, the graphics card question (asked with no window), and whether
antivirus reacts to a program listening on 127.0.0.1.
