# tests/__init__.py — S21 (stage 0.3): a guard for every test module.
# Shyft writes its records into the home (Nook) when there is one. Tests must never write
# into a real person's home, so every test starts with NO home: Shyft's note of where the
# home is points at a file that doesn't exist. Tests that need a home make their own, in a
# temporary folder, and point SHYFT_HOME_NOTE at it.
import os
import tempfile

os.environ["SHYFT_HOME_NOTE"] = os.path.join(tempfile.gettempdir(), "shyft-tests-no-home", "home.json")
