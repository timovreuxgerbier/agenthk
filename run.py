# run.py — Housekeeping Agent entry point: the command line and the run loop.
# What happens to each screenshot (Zippy first, then Pip) lives in harness/pipeline.py.
#
#   python3 run.py                      propose for up to 3 screenshots, default model
#   python3 run.py gemma4:e4b 10        choose model and how many (caps: 10 files, 15 calls)
#   python3 run.py gemma4:e2b all       BATCH: every screenshot in the folder, caps lifted
#                                       (evaluation runs over a whole test set only)
#   python3 run.py gemma4:e2b all --zippy gemma4:e4b
#                                       S10: Zippy on its own model, Pip on the first one.
#                                       Without --zippy, both buddies use the same model.
#   python3 run.py gemma4:e2b all --one-by-one
#                                       S14: the old order (Zippy, Pip, Zippy, Pip...).
#                                       Without it, "all" runs go in chunks of 50: Zippy
#                                       looks at the chunk, then Pip (harness/batch.py).
#   python3 run.py score                compare the latest run against golden/golden.csv
#   python3 run.py score RUN_ID         compare an older run (its id is in trace.jsonl)
#   python3 run.py cost                 S11: time + tokens + cloud estimate, latest run
#   python3 run.py cost RUN_ID          the same for an older run (old runs: time only)
#
# It moves, renames and deletes NOTHING.

import sys
import time

from harness import schema, prefilter, context, trace, caps, gate, pipeline, batch

# Windows terminals default to a code page that crashes on emoji in model output.
sys.stdout.reconfigure(encoding="utf-8")

ONE_BY_ONE = "--one-by-one"


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


def _one_by_one(files, model, zippy_model, texts, copies, limits, run_id):
    """The order before S14: each screenshot goes through Zippy and Pip before the next."""
    for number, image in enumerate(files, start=1):
        label = "[" + str(number) + "/" + str(len(files)) + "] " + image.name
        if pipeline.handle(label, image, model, texts, copies, limits, run_id,
                           zippy_model) == pipeline.STOP:
            return


def propose(model, max_files, batch_mode=False, zippy_model=None, one_by_one=False):
    zippy_model = zippy_model or model
    texts = {"pip": context.read_spec(), "zippy": gate.read_instructions()}
    for file_name, text in (("spec.md", texts["pip"]), ("zippy.md", texts["zippy"])):
        if text is None:
            print("Missing " + file_name + " in the project folder.")
            return
    if batch_mode:
        limits, max_files = batch_caps()
    else:
        limits = caps.RunCaps()
    files = limits.limit_files(prefilter.pick_screenshots(max_files))
    if not files:
        print("No screenshots found. Put 1 to 3 .png or .jpg files in:")
        print("  " + str(schema.SCREENSHOTS))
        return

    chunked = batch_mode and not one_by_one   # capped runs stay one by one (see batch.py)
    run_id = trace.new_run_id()
    who = "model " + model
    if zippy_model != model:
        who = "Zippy on " + zippy_model + ", Pip on " + model
    print("Run " + run_id + ": " + str(len(files)) + " screenshot(s), " + who)
    if chunked:
        print("Order: chunks of " + str(batch.CHUNK_SIZE) + ". Zippy looks at a chunk, then Pip"
              + " works through it, so each model loads once per chunk.")
    else:
        print("Order: one by one (Zippy, then Pip, for each screenshot).")
    print("Zippy looks first; Pip only sees what Zippy clears.")
    print("Nothing will be moved, renamed or deleted.\n")
    run_start = time.time()
    copies = prefilter.find_copies(files)
    step = batch.run if chunked else _one_by_one
    try:
        step(files, model, zippy_model, texts, copies, limits, run_id)
    except pipeline.Stopped as problem:
        print("  " + str(problem))
        return

    print("Done. Total " + str(round(time.time() - run_start, 1)) + " seconds. Trace saved to trace.jsonl")
    print(limits.summary())


def read_args(args):
    """Turn the words after run.py into (pip_model, zippy_model, max_files, batch_mode).
    --zippy MODEL may appear anywhere; without it Zippy uses Pip's model (as before S10).
    --one-by-one is read in main(), so this keeps returning four things."""
    args = [word for word in args if word != ONE_BY_ONE]
    zippy_model = None
    if "--zippy" in args:
        at = args.index("--zippy")
        if at + 1 >= len(args):
            raise ValueError("--zippy needs a model name, for example: --zippy gemma4:e4b")
        zippy_model = args[at + 1]
        del args[at:at + 2]
    model = args[0] if args else schema.DEFAULT_MODEL
    batch_mode = len(args) > 1 and args[1].lower() == "all"
    max_files = schema.DEFAULT_MAX_FILES
    if len(args) > 1 and not batch_mode:
        try:
            max_files = int(args[1])      # any number is still clipped to the 10-file cap
        except ValueError:
            raise ValueError("After the model, write a number or 'all', not: " + args[1])
    return model, zippy_model or model, max_files, batch_mode


def main():
    args = sys.argv[1:]
    if args and args[0] == "score":
        from eval import score
        score.main(args[1] if len(args) > 1 else None)
        return
    if args and args[0] == "cost":
        from eval import cost
        cost.main(args[1] if len(args) > 1 else None)
        return
    try:
        model, zippy_model, max_files, batch_mode = read_args(args)
    except ValueError as problem:
        print(problem)
        return
    propose(model, max_files, batch_mode, zippy_model, ONE_BY_ONE in args)


if __name__ == "__main__":
    main()
