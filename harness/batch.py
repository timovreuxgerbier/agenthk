# harness/batch.py — S14: batching. Lane: Sphinx.
# Zippy looks at a CHUNK of screenshots first, then Pip works through the same chunk.
# Before S14 the run went Zippy, Pip, Zippy, Pip... When the two models don't fit in
# memory together (Qwen + Pip on the Legion; likely both Gemmas on an ordinary laptop),
# every file loaded each model again. Now each model loads once per chunk.
#
# What does NOT change: the steps (pipeline.look and pipeline.finish are the same code
# handle() uses), the prompts, the answers (temperature 0), the trace lines and their
# order. Pip still never sees a file Zippy locked: finish() checks the lock first.
# Why chunks, not the whole run in two passes (Sphinx, S14, option B): Zippy's answers
# wait in memory until Pip's pass writes the trace line, so a crash loses at most one
# chunk, and a long overnight run names files as it goes instead of at the very end.

from harness import pipeline

CHUNK_SIZE = 50   # the Mac set is one chunk, the synthetic set (91) is two


def chunks(items, size=None):
    """Split a list into pieces of at most `size` (default CHUNK_SIZE), in the same order.
    CHUNK_SIZE is read at call time, not when this file loads, so a change to it counts."""
    size = size or CHUNK_SIZE
    items = list(items)
    return [items[start:start + size] for start in range(0, len(items), size)]


def run(images, model, zippy_model, texts, copies, limits, run_id):
    """Run every screenshot, chunk by chunk. Returns pipeline.STOP if a cap stopped it.
    Raises pipeline.Stopped (Ollama missing) like handle() does."""
    total = len(images)
    parts = chunks(images)
    number = 0
    for part_number, part in enumerate(parts, start=1):
        print("=== Chunk " + str(part_number) + "/" + str(len(parts)) + ": Zippy looks at "
              + str(len(part)) + " screenshot(s) ===\n")
        looked = []
        for image in part:
            number += 1
            label = "[" + str(number) + "/" + str(total) + "] " + image.name
            entry = pipeline.look(label, image, model, zippy_model, texts, limits, run_id)
            if entry == pipeline.STOP:
                break
            looked.append((label, image, entry))
        stopped_early = len(looked) < len(part)

        print("\n=== Chunk " + str(part_number) + "/" + str(len(parts)) + ": Pip's turn ("
              + str(len(looked)) + " screenshot(s); locked ones are skipped) ===\n")
        for label, image, entry in looked:
            outcome = pipeline.finish(label, image, entry, model, texts, copies, limits,
                                      announce=True)
            if outcome == pipeline.STOP:
                return pipeline.STOP
        if stopped_early:
            return pipeline.STOP
    return None
