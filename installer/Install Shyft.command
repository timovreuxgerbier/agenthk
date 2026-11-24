#!/bin/bash
# Install Shyft — double-click to set up Shyft for testing. Safe to run again: it skips what's done.
# Does the "Install" part of Sphinx's READ ME: Ollama, the two models, the code, the test set.
DIR="$(cd "$(dirname "$0")" && pwd)"
. "$DIR/shyft_common.sh"
clear
cat <<'EOF'
  Shyft installer
  ---------------
  This sets up Shyft for testing. It will:
    1. check your Mac
    2. install Ollama (free, from ollama.com) if you don't have it
    3. download Rick's and Zippy's models (about 17 GB)
    4. put the Shyft code and the made-up test screenshots in a folder called Shyft
  It only uses made-up screenshots. Nothing of yours is read or sent anywhere.
EOF
pause "Press Return to start (or close this window to cancel)."

say "1/5  Checking your Mac"
[ "$(uname)" = "Darwin" ] || stop "This installer is for Macs."
os=$(sw_vers -productVersion); major=${os%%.*}
[ "$major" -ge 14 ] || stop "Ollama needs macOS 14 (Sonoma) or newer. This Mac has macOS $os."
ok "macOS $os"
ok "$(sysctl -n machdep.cpu.brand_string), $(ram_gb) GB memory"
[ "$(ram_gb)" -ge 8 ] || stop "Shyft needs at least 8 GB of memory. This Mac has $(ram_gb) GB."
[ "$(ram_gb)" -ge 16 ] || warn "8 to 15 GB works, but runs may be slow. That's useful to know too."
ok "$(free_gb) GB free disk space"

say "2/5  Apple's developer tools (they include Python and git)"
if ! xcode-select -p >/dev/null 2>&1; then
  xcode-select --install >/dev/null 2>&1
  stop "A window just opened asking to install Apple's developer tools. Click Install and wait until it finishes (5 to 20 minutes). Then double-click Install Shyft again."
fi
ok "$(python3 --version 2>&1)"
ok "$(git --version)"

say "3/5  Ollama"
if [ -z "$(ollama_bin)" ]; then
  echo "    Installing Ollama with its official installer. It may ask for your Mac password (typing won't show; that's normal)."
  curl -fsSL https://ollama.com/install.sh | sh || stop "Ollama didn't install. Check your internet connection and try again."
fi
OL=$(ollama_bin); [ -n "$OL" ] || stop "Couldn't find Ollama after installing. Open it once from Applications, then try again."
if ! ollama_up; then open -a Ollama >/dev/null 2>&1; fi
wait_ollama || stop "Ollama didn't start. Open it from Applications (look for the llama icon at the top of your screen), then try again."
ok "Ollama is running"

say "4/5  Rick's and Zippy's models"
for m in $MODELS; do
  if has_model "$OL" "$m"; then ok "$m is already here"; continue; fi
  [ "$(free_gb)" -ge 10 ] || stop "Not enough free space for $m. Free up space (about $NEED_GB GB in total), then try again."
  echo "    Downloading $m. This is the long part; keep the Mac on Wi-Fi."
  "$OL" pull "$m" || stop "The download of $m stopped. Run Install Shyft again: it picks up where it left off."
  ok "$m downloaded"
done

say "5/5  Shyft code and test screenshots"
if [ -d "$SHYFT_HOME/.git" ]; then
  git -C "$SHYFT_HOME" pull --ff-only -q && ok "Code updated" || warn "Couldn't update the code; using the copy already here."
else
  git clone -q "$REPO_URL" "$SHYFT_HOME" || stop "Couldn't download the Shyft code. Check your internet connection and try again."
  ok "Code downloaded to your Shyft folder"
fi
[ -f "$DIR/shyft_synthetic_set.zip" ] || stop "The test screenshots (shyft_synthetic_set.zip) are missing from the installer."
unzip -o -q "$DIR/shyft_synthetic_set.zip" -d "$SHYFT_HOME" || stop "Couldn't unpack the test screenshots."
(cd "$SHYFT_HOME" && python3 dev/use_set.py synthetic >/dev/null) || stop "Couldn't switch Shyft to the test screenshots."
ok "91 made-up test screenshots ready"

echo "    Running Shyft's own checks (about a minute)…"
if (cd "$SHYFT_HOME" && python3 -m unittest $TESTS > install_check.txt 2>&1); then ok "All checks passed"
else warn "Some checks failed. That's still useful: the details are in Shyft/install_check.txt"; fi

printf "\n\033[1;32mShyft is installed.\033[0m\nNext: double-click \"Run the Shyft test\".\n"
pause "Press Return to close."
