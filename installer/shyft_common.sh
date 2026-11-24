# shyft_common.sh — shared helpers for "Install Shyft" and "Run the Shyft test".
# Written for the Bash that ships with macOS (3.2): no newer Bash features.

SHYFT_HOME="$HOME/Shyft"                                   # where the code and test set live
REPO_URL="https://github.com/timovreuxgerbier/agenthk.git"
MODELS="gemma4:e4b gemma4:e2b"                             # Zippy, then Rick
NEED_GB=17                                                 # fresh download on Timo's Mac: 9.5 + 7.5 GB
TESTS="tests.test_execute tests.test_golden tests.test_naming tests.test_caps tests.test_gate tests.test_two_models tests.test_cost tests.test_batch tests.test_server tests.test_zoom"

say()  { printf "\n\033[1;32m==>\033[0m \033[1m%s\033[0m\n" "$1"; }
ok()   { printf "    \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "    \033[33m!\033[0m %s\n" "$1"; }
stop() { printf "\n\033[31m✗ %s\033[0m\n\nPress Return to close this window." "$1"; read -r _; exit 1; }
pause() { printf "\n%s " "$1"; read -r _; }

# Where the ollama command is (Terminal may not know it yet right after installing).
ollama_bin() {
  if command -v ollama >/dev/null 2>&1; then command -v ollama
  elif [ -x /Applications/Ollama.app/Contents/Resources/ollama ]; then echo /Applications/Ollama.app/Contents/Resources/ollama
  fi
}
ollama_up()   { curl -s -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; }
wait_ollama() { i=0; while ! ollama_up; do i=$((i + 1)); [ "$i" -gt 60 ] && return 1; sleep 2; done; return 0; }
has_model()   { "$1" list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "$2"; }
free_gb()     { df -g "$HOME" | awk 'NR==2 {print $4}'; }
ram_gb()      { echo $(( $(sysctl -n hw.memsize) / 1073741824 )); }
