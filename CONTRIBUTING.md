# How we work on this together

Four people coding at once, one app at the end. These rules are what make that work.

## Who owns which file

| Lane | Owner | Files |
| --- | --- | --- |
| Before the model | Raaghavi | `harness/prefilter.py` · `harness/context.py` · `harness/router.py` · wording of `spec.md` |
| After the model | Timo | `harness/check.py` · later `caps.py`, `execute.py`, `rules.py`, `eval/cost.py` |
| Guardrails, traces, golden set, Quarantine | Sphinx | `harness/trace.py` · `eval/score.py` · later `guardrails.py`, `ui/` |
| Evaluation layers | Ana | later `eval/judge.py`, `eval/rubric.md` |
| **Shared: team decision only** | everyone | `harness/schema.py` · `run.py` · this file |

Edit your own files freely. If you need a change in someone else's file, ask them, or open a PR and tag them.

## The rules

1. **Python standard library only.** No `pip install`. Every package we add makes the installer harder later. If you think you need one, bring it to the team.
2. **`harness/schema.py` is the only shared vocabulary.** Actions, proposal fields, trace fields, folder names and paths live there and nowhere else. Never redefine them in your own file.
3. **Lane files import only from `schema.py`** (plus the standard library). `run.py` is the only file that imports across lanes. This is what keeps merge conflicts close to zero.
4. **Paths are `pathlib.Path`, never strings.** We are on both Mac and Windows.
5. **Keep every file under about 150 lines.** If yours grows, split it.
6. **Nothing deletes. Ever.** No `unlink`, `rmtree`, `os.remove` or `send2trash` in `harness/`. "To Be Deleted" is a folder a human empties.
7. **The model never touches files.** Only our code moves or renames, only after a person approves, only inside the agent's own folders.
8. **Never commit personal data.** Screenshots, traces, golden labels and rules are in `.gitignore`. Check `git status` before every commit. If you see a screenshot listed, stop.
9. **Every behaviour change goes through the golden set.** Run `python3 run.py score` before and after, and paste both pass rates in your PR.

## Branches

- Never commit straight to `main`.
- One branch per change, starting with your name: `raaghavi/prefilter-seen-json`, `timo/caps`, `sphinx/trace-redaction`, `ana/judge`.
- Open a pull request into `main`. Timo merges.
- Before starting new work: `git checkout main`, then `git pull`, then make your branch.
