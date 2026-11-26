#!/bin/bash
# Run the Shyft test — double-click after "Install Shyft". Does steps 2 to 5 of Sphinx's READ ME:
# starts Ollama with a longer memory window, records memory every 30 s, runs A (two models) and
# B (one model) with score and cost, then puts everything to send back in one folder on the Desktop.
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/shyft_common.sh"
clear
cd "$SHYFT_HOME" 2>/dev/null || stop "Shyft isn't installed yet. Double-click \"Install Shyft\" first."
OL=$(ollama_bin); [ -n "$OL" ] || stop "Ollama isn't installed yet. Double-click \"Install Shyft\" first."
cat <<'EOF'
  Shyft test
  ----------
  Two runs on 91 made-up screenshots. Takes 30 to 90 minutes, mostly waiting.
    - Plug your Mac in. It will stay awake by itself until the test ends.
    - Leave this window open. It can look frozen; it's working.
    - If something stops or the Mac struggles, that's a result too: you'll still get a results folder.
EOF
pause "Press Return to start."

OUT="$HOME/Desktop/Shyft test results"; mkdir -p "$OUT"
START=$(mktemp)                                   # marks the start time, to find today's result files
rm -f ps_timo.txt "$OUT/what_happened.txt"
{ echo "Date: $(date)"
  echo "Chip: $(sysctl -n machdep.cpu.brand_string)"
  echo "Memory: $(ram_gb) GB"
  echo "Mac model: $(sysctl -n hw.model)"
  echo "Year (Apple menu > About This Mac): ____ please type it here"
  echo "macOS: $(sw_vers -productVersion)"
  echo "Free disk: $(free_gb) GB"
  echo "Python: $(python3 --version 2>&1)"; } > "$OUT/my_mac.txt"

say "Starting Ollama with a longer memory window"
osascript -e 'quit app "Ollama"' >/dev/null 2>&1
i=0; while ollama_up && [ "$i" -lt 15 ]; do sleep 1; i=$((i + 1)); done
if ollama_up; then   # something kept Ollama running: say so, so the results aren't misread
  warn "Ollama didn't quit, so this test runs WITHOUT the longer memory window."
  echo "Note: ran without OLLAMA_CONTEXT_LENGTH=16384 (Ollama didn't quit)" >> "$OUT/what_happened.txt"
fi
OLLAMA_CONTEXT_LENGTH=16384 "$OL" serve > "$SHYFT_HOME/ollama_serve.log" 2>&1 &
SERVE=$!
wait_ollama || stop "Ollama didn't start. Restart your Mac, then double-click \"Run the Shyft test\" again."
ok "Ollama is running"

caffeinate -dimsu & AWAKE=$!                      # keeps the Mac awake while this window runs
( while true; do curl -s http://127.0.0.1:11434/api/ps; echo; memory_pressure 2>/dev/null | tail -1; sleep 30; done ) >> ps_timo.txt 2>/dev/null &
MEMLOG=$!
cleanup() { kill "$MEMLOG" "$AWAKE" "$SERVE" 2>/dev/null; }
trap cleanup EXIT

step() {   # runs one step; if it fails, notes it and carries on
  say "$1"; shift
  if bash -c "set -o pipefail; $*"; then ok "done"
  else warn "This step stopped. That's a result too."; echo "Stopped: $* ($(date))" >> "$OUT/what_happened.txt"; fi
}
step "Run A: Rick ($RICK) with Zippy ($ZIPPY)" "python3 run.py $RICK all --zippy $ZIPPY 2>&1 | tee run_A.txt"
step "Scoring run A" "python3 run.py score"
step "Cost of run A" "python3 run.py cost"
step "Run B: Rick only ($RICK)" "python3 run.py $RICK all 2>&1 | tee run_B.txt"
step "Scoring run B" "python3 run.py score"
step "Cost of run B" "python3 run.py cost"

say "Collecting your results"
find golden -maxdepth 1 -newer "$START" \( -name 'cost_synthetic_*' -o -name 'score_synthetic_*' \) -exec cp {} "$OUT/" \;
cp ps_timo.txt run_A.txt run_B.txt "$OUT/" 2>/dev/null
low=$(grep -o 'free percentage: [0-9]*' ps_timo.txt | grep -o '[0-9]*$' | sort -n | head -1)
[ -n "$low" ] && echo "Lowest free memory during the runs: ${low}%" >> "$OUT/my_mac.txt"
cleanup; trap - EXIT
open -a Ollama >/dev/null 2>&1                    # put Ollama back to normal
ok "$(ls "$OUT" | wc -l | tr -d ' ') files in \"Shyft test results\" on your Desktop"
open "$OUT"
printf "\n\033[1;32mDone.\033[0m Type your Mac's year in my_mac.txt, then send the whole\n\"Shyft test results\" folder to Sphinx. It holds only made-up file names, timings and model names.\n"
pause "Press Return to close."
