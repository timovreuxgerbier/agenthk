#!/bin/bash
# Install Shyft — double-click to set up Shyft for testing. Safe to run again: it skips what's done.
# Kit 3: the Shyft code comes INSIDE the kit (one pinned commit, the same as the Windows kit; no git, no main).
# It writes down everything it brings (see shyft_common.sh: RECORD), so "Remove Shyft" takes away only that.
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/shyft_common.sh"
clear
cat <<EOF
  Shyft installer ($KIT_VERSION)
  ---------------
  This sets up Shyft for testing. It will:
    1. check your Mac
    2. install Ollama (free, from ollama.com) if you don't have it
    3. download Rick's and Zippy's models (about 11.2 GB) if they aren't here yet
    4. unpack the Shyft code and the made-up test screenshots into a folder called Shyft
       (both come inside this kit)
  It only uses made-up screenshots. Nothing of yours is read or sent anywhere.
  Anything already on your Mac stays as it is.
EOF
pause "Press Return to start (or close this window to cancel)."

say "1/5  Checking your Mac"
[ "$(uname)" = "Darwin" ] || stop "This installer is for Macs."
CODE_ZIP=$(code_zip "$DIR")                       # kit files checked first, before any download
[ -f "$SHYFT_HOME/.shyft_kit_commit" ] || [ -n "$CODE_ZIP" ] || stop "The Shyft code (a file named agenthk-$(echo "$CODE_COMMIT" | cut -c1-7)...zip) is missing from the installer. Download the whole kit again."
[ -f "$DIR/shyft_synthetic_set.zip" ] || stop "The test screenshots (shyft_synthetic_set.zip) are missing from the installer. Download the whole kit again."
if [ -d "$SHYFT_HOME" ] && ! has_record shyft_folder yes; then
  stop "There is already a folder called Shyft in your home folder that this kit didn't make (it may be yours, or from an earlier tester kit that kept no note). To keep it safe, the kit stops here and changes nothing. Rename or move that folder, then run this again."
fi
os=$(sw_vers -productVersion); major=${os%%.*}
[ "$major" -ge 14 ] || stop "Ollama needs macOS 14 (Sonoma) or newer. This Mac has macOS $os."
ok "macOS $os"
ok "$(sysctl -n machdep.cpu.brand_string), $(ram_gb) GB memory"
[ "$(ram_gb)" -ge 8 ] || stop "Shyft needs at least 8 GB of memory. This Mac has $(ram_gb) GB."
[ "$(ram_gb)" -ge 16 ] || warn "This Mac has $(ram_gb) GB of memory. Shyft may be slow here; that's useful to know too."
ok "$(free_gb) GB free disk space"

say "2/5  Apple's developer tools (they include Python)"
if ! xcode-select -p >/dev/null 2>&1; then
  xcode-select --install >/dev/null 2>&1
  stop "A window just opened asking to install Apple's developer tools. Click Install and wait until it finishes (5 to 20 minutes). Then double-click Install Shyft again."
fi
ok "$(python3 --version 2>&1)"

say "3/5  Ollama"
if [ -z "$(ollama_bin)" ]; then
  echo "    Installing Ollama with its official installer. It may ask for your Mac password (typing won't show; that's normal)."
  add_record program "Ollama (quit it from the llama icon at the top of the screen, then drag Ollama from Applications to the Trash)"
  curl -fsSL https://ollama.com/install.sh | sh || stop "Ollama didn't install. Check your internet connection and try again."
else ok "Ollama was already here: using it as it is"; fi
OL=$(ollama_bin); [ -n "$OL" ] || stop "Couldn't find Ollama after installing. Open it once from Applications, then try again."
if ! ollama_up; then open -a Ollama >/dev/null 2>&1; fi
wait_ollama || stop "Ollama didn't start. Open it from Applications (look for the llama icon at the top of your screen), then try again."
ok "Ollama is running"
cloud_report || stop "$TOO_OLD"                   # before the long downloads
ok "Ollama can report its cloud setting"

say "4/5  Rick's and Zippy's models"
for m in $MODELS; do
  if has_model "$OL" "$m"; then
    if has_record model "$m"; then ok "$m is here (downloaded by this kit earlier)"; else ok "$m was already on this Mac: the kit will leave it there"; fi
    continue
  fi
  [ "$(free_gb)" -ge 10 ] || stop "Not enough free space for $m. Free up space (about $NEED_GB GB in total), then try again."
  add_record model "$m"                           # written BEFORE downloading, so even a half download is ours to remove
  echo "    Downloading $m. This is the long part; keep the Mac on Wi-Fi."
  "$OL" pull "$m" || stop "The download of $m stopped. Run Install Shyft again: it picks up where it left off."
  ok "$m downloaded"
done
for m in $MODELS; do   # D27: exactly the measured builds, or stop and say so plainly
  id=$(model_id "$OL" "$m")
  [ "$id" = "$(expected_id "$m")" ] || stop "$m here is not the build Shyft was measured with (id ${id:-none}, expected $(expected_id "$m")). Please tell the Shyft team, and send them the two lines \"ollama list\" shows."
done
ok "Both models are the exact builds Shyft was measured with"

say "5/5  Shyft code and test screenshots"
if [ "$(cat "$SHYFT_HOME/.shyft_kit_commit" 2>/dev/null)" = "$CODE_COMMIT" ]; then ok "Shyft code is already here"
else
  [ -d "$SHYFT_HOME" ] && rm -rf "$SHYFT_HOME"    # only ever our own folder (checked in step 1)
  TMP="$KIT_DIR/unpack"; rm -rf "$TMP"; mkdir -p "$TMP"
  unzip -q "$CODE_ZIP" -d "$TMP" || stop "Couldn't unpack the Shyft code. Download the whole kit again."
  [ -d "$TMP/agenthk-$CODE_COMMIT" ] || { rm -rf "$TMP"; stop "The Shyft code in the kit isn't version $(echo "$CODE_COMMIT" | cut -c1-7). Ask the team for the right kit."; }
  add_record shyft_folder yes
  mv "$TMP/agenthk-$CODE_COMMIT" "$SHYFT_HOME" && echo "$CODE_COMMIT" > "$SHYFT_HOME/.shyft_kit_commit"
  rm -rf "$TMP"
  ok "Shyft code unpacked (version $(echo "$CODE_COMMIT" | cut -c1-7))"
fi
if [ "$(cat "$SHYFT_HOME/golden/active_set.txt" 2>/dev/null)" = "synthetic" ]; then ok "Made-up test screenshots already loaded"
else
  unzip -o -q "$DIR/shyft_synthetic_set.zip" -d "$SHYFT_HOME" || stop "Couldn't unpack the test screenshots."
  (cd "$SHYFT_HOME" && python3 dev/use_set.py synthetic >/dev/null) || stop "Couldn't switch Shyft to the test screenshots."
  ok "91 made-up test screenshots ready"
fi

echo "    Running Shyft's own checks (about a minute)…"
if (cd "$SHYFT_HOME" && python3 -m unittest $TESTS > install_check.txt 2>&1); then ok "All checks passed"
else warn "Some checks failed. That's still useful: the details are in Shyft/install_check.txt"; fi

printf "\n\033[1;32mShyft is installed.\033[0m\nNext: double-click \"Run the Shyft test\".\n"
pause "Press Return to close."
