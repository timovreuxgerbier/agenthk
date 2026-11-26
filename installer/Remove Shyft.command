#!/bin/bash
# Remove Shyft — gives back the space: deletes the Shyft folder and the two models (about 11.2 GB).
# Keeps the Ollama app (other apps may use it) and your "Shyft test results" folder.
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/shyft_common.sh"
clear
cat <<'EOF'
  Remove Shyft
  ------------
  This deletes:
    - the Shyft folder in your home folder (code and made-up test screenshots)
    - Rick's and Zippy's models (about 11.2 GB)
  It keeps the Ollama app and the "Shyft test results" folder on your Desktop.
EOF
pause "Press Return to remove Shyft (or close this window to cancel)."

OL=$(ollama_bin)
if [ -n "$OL" ]; then
  ollama_up || { open -a Ollama >/dev/null 2>&1; wait_ollama; }
  for m in $MODELS; do
    if has_model "$OL" "$m"; then "$OL" rm "$m" >/dev/null && ok "Removed $m" || warn "Couldn't remove $m"; fi
  done
fi
[ -d "$SHYFT_HOME" ] && rm -rf "$SHYFT_HOME" && ok "Removed the Shyft folder"
printf "\nDone. To remove Ollama too: quit it (llama icon at the top of the screen > Quit), then drag Ollama from Applications to the Trash.\n"
pause "Press Return to close."
