# installer/: the Shyft tester packages (Mac and Windows)

What testers download: **Shyft-Tester.dmg**. Inside: READ ME FIRST, three double-click scripts,
and the made-up test screenshots. The scripts automate Sphinx's test steps (install, two runs, results).

| File | What it does |
|---|---|
| `Install Shyft.command` | Checks the Mac, installs Ollama (official script from ollama.com), downloads gemma4:e4b-it-q4_K_M + gemma4:e2b-it-q4_K_M (decision D27, checked by id), clones this repo into `~/Shyft`, unpacks the test set, runs the unit tests. Safe to run again. |
| `Run the Shyft test.command` | Starts Ollama with `OLLAMA_CONTEXT_LENGTH=16384`, logs memory every 30 s, runs A (e2b + Zippy e4b) and B (e2b), score + cost after each, then collects results in `~/Desktop/Shyft test results`. |
| `Remove Shyft.command` | Deletes `~/Shyft` and the two models (about 11.2 GB). Keeps Ollama and the results. |
| `shyft_common.sh` | Shared settings (models, repo, space needed) and helpers. |
| `make_dmg.sh` | Builds the DMG. **Mac only.** |

## Build and publish (on a Mac)
1. Put `shyft_synthetic_set.zip` (from Sphinx) in this folder. It is test data, so Git ignores it.
2. `bash installer/make_dmg.sh` → `installer/Shyft-Tester.dmg`
3. **Test it yourself first**: open the DMG and run all three scripts.
4. On GitHub: Releases > Draft a new release > tag `tester-v1` > attach `Shyft-Tester.dmg` > Publish.
   The download page links to `releases/latest/download/Shyft-Tester.dmg`, so the newest release is always used.

## Known limits (be honest with testers)
- **Not signed or notarized.** That needs a paid Apple Developer account. Every tester sees
  "Apple could not verify…" once per script and must click **Open Anyway** in System Settings.
- The Ollama installer may ask for the Mac password (it adds the `ollama` command).
- Untested on Intel Macs. Ollama runs there on the CPU only, so expect very slow runs.

## Windows kit (`installer/windows/`)
What Windows testers download: **Shyft-Tester-Windows.zip**. They extract it, then double-click
three `.bat` files. Each one runs a PowerShell script from the `files/` folder (plain text, readable in Notepad).

| File | What it does |
|---|---|
| `install.ps1` | Checks Windows 10 22H2+ / memory / disk; installs Python and git with winget if missing; Ollama with its official script (no admin needed); both models; clones the repo to `%USERPROFILE%\Shyft`; unpacks the test set; runs the unit tests. |
| `run_test.ps1` | Same steps as the Mac version, with Windows' own keep-awake setting. Results in `Desktop\Shyft test results`, PC details in `my_pc.txt` (including the graphics card). |
| `remove.ps1` | Deletes the Shyft folder and the two models. Keeps Ollama and the results. |
| `make_windows_kit.sh` | Builds the zip (Mac or Linux). |

Build: `bash installer/windows/make_windows_kit.sh` → attach `Shyft-Tester-Windows.zip` to the same release.
Scripts are written for Windows PowerShell 5.1 and kept plain ASCII (5.1 misreads other characters).
Windows shows "Windows protected your PC" once: **More info → Run anyway** (unsigned, like the Mac kit).

## Keep out of Git
Add these to `.gitignore`: `installer/shyft_synthetic_set.zip`, `installer/Shyft-Tester.dmg`,
`installer/windows/Shyft-Tester-Windows.zip`.
