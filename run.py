# run.py — Housekeeping Agent entry point: the command line and the run loop.
# What happens to each screenshot (Zippy first, then Pip) lives in harness/pipeline.py.
#
#   python3 run.py                      propose for up to 3 screenshots, default model
#   python3 run.py gemma4:e4b 10        choose model and how many (caps: 10 files, 15 calls)
#   python3 run.py gemma4:e2b all       BATCH: every screenshot in the folder, caps lifted
#                                       (evaluation runs over a whole test set only)
#   python3 run.py score                compare the latest run against golden/golden.csv
#
# It moves, renames and deletes NOTHING.

import sys
import time

from harness import schema, prefilter, context, trace, caps, gate, pipeline

# Windows terminals default to a code page that crashes on emoji in model output.
sys.stdout.reconfigure(encoding="utf-8")


def batch_caps():
    """Caps for ONE evaluation run over the whole folder. Normal runs never use this:
    the proposal's limits (10 files, 15 calls, 5 minutes) stay the default."""
    total = len(prefilter.pick_screenshots(10 ** 6))
    limits = caps.RunCaps(max_files=total, max_calls=2 * total + 10, max_seconds=6 * 3600)
    print("BATCH MODE: evaluation run over the whole folder (" + str(total) + " files).")
    print("Caps lifted for this run only: up to " + str(limits.max_calls) + " model calls, "
          + str(limits.max_seconds // 3600) + " hours. Normal runs keep "
          + str(schema.MAX_FILES_PER_RUN) + " files, " + str(schema.MAX_CALLS_PER_RUN)
          + " calls, " + str(schema.MAX_RUN_SECONDS) + " s.\n")
    return limits, total


def propose(model, max_files, batch_mode=False):
    texts = {"pip": context.read_spec(), "zippy": gate.read_instructions()}
    for file_name, text in (("spec.md", texts["pip"]), ("zippy.md", texts["zippy"])):
        if text is None:
            print("Missing " + file_name + " in the project folder.")
            return
    if batch_mode:
        limits, max_files = batch_caps()
    else:
        limits = caps.RunCaps()
    batch = limits.limit_files(prefilter.pick_screenshots(max_files))
    if not batch:
        print("No screenshots found. Put 1 to 3 .png or .jpg files in:")
        print("  " + str(schema.SCREENSHOTS))
        return

    run_id = trace.new_run_id()
    print("Run " + run_id + ": " + str(len(batch)) + " screenshot(s), model " + model)
    print("Zippy looks first; Pip only sees what Zippy clears.")
    print("Nothing will be moved, renamed or deleted.\n")
    run_start = time.time()
    copies = prefilter.find_copies(batch)

    for number, image in enumerate(batch, start=1):
        label = "[" + str(number) + "/" + str(len(batch)) + "] " + image.name
        try:
            outcome = pipeline.handle(label, image, model, texts, copies, limits, run_id)
        except pipeline.Stopped as problem:
            print("  " + str(problem))
            return
        if outcome == pipeline.STOP:
            break

    print("Done. Total " + str(round(time.time() - run_start, 1)) + " seconds. Trace saved to trace.jsonl")
    print(limits.summary())


def main():
    args = sys.argv[1:]
    if args and args[0] == "score":
        from eval import score
        score.main()
        return
    model = args[0] if args else schema.DEFAULT_MODEL
    batch_mode = len(args) > 1 and args[1].lower() == "all"
    max_files = schema.DEFAULT_MAX_FILES
    if len(args) > 1 and not batch_mode:
        max_files = int(args[1])          # any number is still clipped to the 10-file cap
    propose(model, max_files, batch_mode)


if __name__ == "__main__":
    main()
