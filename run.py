# run.py — Housekeeping Agent entry point. The ONLY file that imports from every lane.
#
#   python3 run.py                      propose for up to 3 screenshots, default model
#   python3 run.py gemma4:e2b 30        choose model and how many screenshots
#   python3 run.py score                compare the latest run against golden/golden.csv
#
# It moves, renames and deletes NOTHING.

import sys
import time
import urllib.error

from harness import schema, prefilter, context, router, check, trace

# Windows terminals default to a code page that crashes on emoji in model output.
sys.stdout.reconfigure(encoding="utf-8")


def show(proposal, problems, flagged):
    if proposal is None:
        print("  REJECTED by code check: " + ", ".join(problems))
        return
    print("  Action:      " + str(proposal.get("action")))
    print("  Reason:      " + str(proposal.get("reason")))
    print("  Why saved:   " + str(proposal.get("why_saved_guess")) + "  (a guess)")
    if proposal.get("new_name"):
        print("  New name:    " + str(proposal.get("new_name")))
    print("  Confidence:  " + str(proposal.get("confidence")))
    if problems:
        print("  CODE CHECK:  " + ", ".join(problems))
    if flagged:
        print("  FLAGGED for review: the agent is unsure.")


def propose(model, max_files):
    spec_text = context.read_spec()
    if spec_text is None:
        print("Missing spec.md in the project folder.")
        return
    batch = prefilter.pick_screenshots(max_files)
    if not batch:
        print("No screenshots found. Put 1 to 3 .png or .jpg files in:")
        print("  " + str(schema.SCREENSHOTS))
        return

    run_id = trace.new_run_id()
    print("Run " + run_id + ": " + str(len(batch)) + " screenshot(s), model " + model)
    print("Nothing will be moved, renamed or deleted.\n")
    run_start = time.time()

    for number, image in enumerate(batch, start=1):
        print("[" + str(number) + "/" + str(len(batch)) + "] " + image.name + " ... thinking")
        started = time.time()
        try:
            raw = router.ask(model, context.build_messages(spec_text, image))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                print("  The model isn't downloaded. In a terminal run: ollama pull " + model)
            else:
                print("  Ollama returned an error: " + str(error.code) + " "
                      + error.read().decode("utf-8", "replace"))
            return
        except urllib.error.URLError:
            print("  Can't reach Ollama. Open the Ollama app, then run this again.")
            return
        except TimeoutError:
            print("  The model took over 5 minutes and was stopped. Skipping this one.\n")
            continue
        seconds = round(time.time() - started, 1)

        proposal, problems = check.check_proposal(raw)
        flagged = check.is_flagged(proposal, problems)
        show(proposal, problems, flagged)
        print("  Took " + str(seconds) + " seconds\n")

        trace.write({
            "run_id": run_id, "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "file": image.name, "model": model, "seconds": seconds,
            "raw_output": raw, "check_problems": problems,
            "flagged": flagged, "user_decision": None,
        })

    print("Done. Total " + str(round(time.time() - run_start, 1)) + " seconds. Trace saved to trace.jsonl")


def main():
    args = sys.argv[1:]
    if args and args[0] == "score":
        from eval import score
        score.main()
        return
    model = args[0] if args else schema.DEFAULT_MODEL
    max_files = int(args[1]) if len(args) > 1 else schema.DEFAULT_MAX_FILES
    propose(model, max_files)


if __name__ == "__main__":
    main()
