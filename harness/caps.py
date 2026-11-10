# harness/caps.py — Lane: Timo (after the model)
# Hard limits for one run: how many files, how many model calls, how much time.
# Our code enforces them, not the model. Limits live in schema.py.
#
#   caps = RunCaps()                 start the clock
#   batch = caps.limit_files(batch)  never more than MAX_FILES_PER_RUN
#   stop = caps.check()              None = go ahead, otherwise the reason to stop
#   caps.record_call()               after every model call
#   caps.summary()                   one line for the end of the run

import time

from harness import schema


class RunCaps:
    def __init__(self, max_files=None, max_calls=None, max_seconds=None, clock=time.monotonic):
        self.max_files = max_files if max_files is not None else schema.MAX_FILES_PER_RUN
        self.max_calls = max_calls if max_calls is not None else schema.MAX_CALLS_PER_RUN
        self.max_seconds = max_seconds if max_seconds is not None else schema.MAX_RUN_SECONDS
        self.clock = clock
        self.started = clock()
        self.calls = 0

    def limit_files(self, files):
        """Return at most max_files items from the list."""
        return list(files)[: self.max_files]

    def seconds_used(self):
        return self.clock() - self.started

    def check(self):
        """Return None if another model call is allowed, otherwise a plain-language reason."""
        if self.calls >= self.max_calls:
            return "call limit reached (" + str(self.max_calls) + " model calls per run)"
        if self.seconds_used() >= self.max_seconds:
            return "time limit reached (" + str(self.max_seconds) + " seconds per run)"
        return None

    def record_call(self):
        self.calls += 1

    def summary(self):
        return ("Used " + str(self.calls) + "/" + str(self.max_calls) + " model calls, "
                + str(round(self.seconds_used(), 1)) + "/" + str(self.max_seconds) + " seconds.")
