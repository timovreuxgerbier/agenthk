# agenthk — Housekeeping Agent

A local AI agent that proposes how to sort your screenshots. Group Red, PSDS 5330 (Parsons, Fall 2026).

It runs **only on your own computer** through [Ollama](https://ollama.com). Nothing leaves the machine. In this version it **only proposes**: it moves, renames and deletes nothing.

## Quick start

1. Install Ollama and Python 3.11 or newer. No other packages are needed.
2. Download a model (the small one is fine for testing):
   ```
   ollama pull gemma4:e2b
   ```
3. Put 1 to 3 screenshots in the `screenshots/` folder.
4. From this folder, run:
   ```
   python3 run.py gemma4:e2b
   ```
   On Windows, if `python3` isn't found, use `python` instead.

## Measuring it (golden set)

```
python3 run.py score          # first time: creates golden/golden.csv for you to fill in
python3 run.py gemma4:e2b 30  # run on up to 30 screenshots
python3 run.py score          # pass rate, mistake patterns, confidence check
```

Label `golden/golden.csv` **before** you look at what the agent said.

## If Ollama crashes with a CUDA error

Your graphics card isn't supported by Ollama's built-in GPU code. Run on the CPU instead. Quit Ollama from the tray, then in a terminal that you leave open:

- Windows (PowerShell): `$env:CUDA_VISIBLE_DEVICES="-1"; ollama serve`
- Mac/Linux: `CUDA_VISIBLE_DEVICES=-1 ollama serve`

## Layout

```
run.py            entry point (the only file that imports from every lane)
spec.md           the agent's task and rules
harness/          the agent's working parts, one small file per job
eval/             measuring the agent
golden/           your labels (never committed)
screenshots/      your screenshots (never committed)
```

Before changing anything, read **CONTRIBUTING.md**.
