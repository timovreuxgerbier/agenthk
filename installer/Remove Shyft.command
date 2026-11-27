#!/bin/bash
# Remove Shyft — takes away ONLY what this kit brought (see shyft_common.sh: RECORD): the models it
# downloaded and the Shyft folder it made. Never uninstalls programs by itself.
# Keeps the "Shyft test results" folder on your Desktop.
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/shyft_common.sh"
clear
cat <<'TXT'
  Remove Shyft
  ------------
  This removes only what the tester kit brought to your Mac:
    - the Rick and Zippy models it downloaded (up to about 11.2 GB)
    - the Shyft folder it made in your home folder
  Anything that was already on your Mac stays. Your "Shyft test results" folder stays.
  Programs the kit installed are NOT removed automatically: you'll see how to remove them.
TXT
pause "Press Return to remove (or close this window to cancel)."
failed=""

say "Models"
OL=$(ollama_bin)
if [ -z "$OL" ]; then ok "Ollama isn't installed, so there are no models to remove"
else
  ollama_up || { open -a Ollama >/dev/null 2>&1; wait_ollama; }
  for m in $MODELS; do
    if has_record model "$m"; then
      if has_model "$OL" "$m"; then
        if "$OL" rm "$m" >/dev/null 2>&1; then ok "Removed $m"; else warn "Couldn't remove $m"; failed=yes; fi
      else
        warn "$m was only partly downloaded, so it can't be removed by name and may still use some space."
        echo "    To clear it: run \"Install Shyft\" to finish the download, then run \"Remove Shyft\" again."
        failed=yes                                   # keep the kit's notes so the next Remove still knows it's ours
      fi
    elif has_model "$OL" "$m"; then ok "Left $m: it was already on this Mac before the kit"; fi
  done
fi

say "Shyft folder"
if has_record shyft_folder yes; then
  if [ -d "$SHYFT_HOME" ]; then
    if rm -rf "$SHYFT_HOME"; then ok "Removed the Shyft folder"; else warn "Couldn't remove the Shyft folder"; failed=yes; fi
  else ok "The Shyft folder is already gone"; fi
elif [ -d "$SHYFT_HOME" ]; then ok "Left the Shyft folder alone: this kit didn't make it"; fi

say "What stays installed"
progs=$(records program)
if [ -z "$progs" ]; then ok "The kit didn't install any programs"
else
  echo "    The kit installed these programs. Remove them yourself if you don't want them:"
  echo "$progs" | while IFS= read -r p; do echo "      - $p"; done
fi

if [ -z "$failed" ]; then rm -rf "$KIT_DIR"; ok "Done. The kit's own notes are removed too."
else warn "Some things couldn't be removed. Run \"Remove Shyft\" again later; the kit kept its notes for that."; fi
pause "Press Return to close."
