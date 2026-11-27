# shyft_common.sh — shared helpers for "Install Shyft", "Run the Shyft test" and "Remove Shyft".
# Written for the Bash that ships with macOS (3.2): no newer Bash features.

KIT_VERSION="kit 3"
CODE_COMMIT="524117b648f9cbf0db445e4c43855dc028b19763"   # the ONE version of Shyft both kits test (main, Nov 27: cloud lock, where-checks, Nook, records)
SHYFT_HOME="$HOME/Shyft"                                   # where the code and test set live
KIT_DIR="$HOME/Library/Application Support/ShyftTesterKit" # the kit's own notes: what it brought
RECORD="$KIT_DIR/record.txt"                               # written BEFORE each step, so a failed install still knows
# Decision D27 (Nov 25): exactly these two model builds on every platform, checked by id after install.
# (On a Mac the short names gemma4:e4b and gemma4:e2b download different builds, about 17 GB.)
ZIPPY="gemma4:e4b-it-q4_K_M"; ZIPPY_ID="dc35e8d9c606"      # 6.6 GB
RICK="gemma4:e2b-it-q4_K_M";  RICK_ID="b37049369adf"       # 4.6 GB
MODELS="$ZIPPY $RICK"                                      # Zippy, then Rick: 11.2 GB together
NEED_GB=18                                                 # 11.2 models + 4 for Ollama + 2 spare
TESTS="tests.test_execute tests.test_golden tests.test_naming tests.test_caps tests.test_gate tests.test_two_models tests.test_cost tests.test_batch tests.test_server tests.test_zoom tests.test_requirements tests.test_check_misses tests.test_cloud_lock tests.test_sync_check tests.test_disk_check tests.test_where_check tests.test_home tests.test_records"   # 169 tests (main 524117b)

say()  { printf "\n\033[1;32m==>\033[0m \033[1m%s\033[0m\n" "$1"; }
ok()   { printf "    \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "    \033[33m!\033[0m %s\n" "$1"; }
stop() { printf "\n\033[31m✗ %s\033[0m\n\nPress Return to close this window." "$1"; read -r _; exit 1; }
pause() { printf "\n%s " "$1"; read -r _; }

# What the kit brought, one "kind=value" line each: shyft_folder, model, program.
add_record() { mkdir -p "$KIT_DIR"; grep -qxF "$1=$2" "$RECORD" 2>/dev/null || echo "$1=$2" >> "$RECORD"; }
has_record() { grep -qxF "$1=$2" "$RECORD" 2>/dev/null; }
records()    { grep "^$1=" "$RECORD" 2>/dev/null | sed "s/^$1=//"; }

# Where the ollama command is (Terminal may not know it yet right after installing).
ollama_bin() {
  if command -v ollama >/dev/null 2>&1; then command -v ollama
  elif [ -x /Applications/Ollama.app/Contents/Resources/ollama ]; then echo /Applications/Ollama.app/Contents/Resources/ollama
  fi
}
ollama_up()   { curl -s -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; }
wait_ollama() { i=0; while ! ollama_up; do i=$((i + 1)); [ "$i" -gt 60 ] && return 1; sleep 2; done; return 0; }
# Shyft's cloud lock asks Ollama (/api/status) whether its cloud is off, before every run. Ollama older than
# 0.40.17 can't answer, so every run would stop. The kit never updates Ollama: it checks and says so instead.
cloud_report() { curl -s -m 5 http://127.0.0.1:11434/api/status 2>/dev/null | grep -q '"disabled"'; }
TOO_OLD="Your Ollama is too old for this version of Shyft: it can't say whether its cloud is off, and Shyft checks that before every run. The kit never changes your Ollama, so please update it yourself from ollama.com/download, then run this again."
has_model()   { "$1" list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qix "$2"; }   # -i: in case Ollama lists names in another case
model_id()    { "$1" list 2>/dev/null | awk -v m="$2" 'NR>1 && tolower($1)==tolower(m) {print $2}'; }   # the ID column, or nothing
expected_id() { if [ "$1" = "$ZIPPY" ]; then echo "$ZIPPY_ID"; elif [ "$1" = "$RICK" ]; then echo "$RICK_ID"; fi; }
free_gb()     { df -g "$HOME" | awk 'NR==2 {print $4}'; }
ram_gb()      { echo $(( $(sysctl -n hw.memsize) / 1073741824 )); }
code_zip()    { ls "$1"/agenthk-"$(echo "$CODE_COMMIT" | cut -c1-7)"*.zip 2>/dev/null | head -1; }   # GitHub "Download ZIP" of CODE_COMMIT
