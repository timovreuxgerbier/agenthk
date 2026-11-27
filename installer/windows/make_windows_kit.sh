#!/bin/bash
# make_windows_kit.sh - builds Shyft-Tester-Windows.zip. Works on a Mac or Linux (needs zip).
# Before running: put shyft_synthetic_set.zip (from Sphinx) and the code zip agenthk-524117b...zip
# (GitHub "Download ZIP" of the pinned commit) in installer/. Neither goes into Git.
# Run it with:   bash installer/windows/make_windows_kit.sh
set -e
cd "$(dirname "$0")"
[ -f ../shyft_synthetic_set.zip ] || { echo "Put shyft_synthetic_set.zip in the installer folder first."; exit 1; }
SHA=$(grep -o 'CodeCommit = "[0-9a-f]*"' common.ps1 | grep -o '[0-9a-f]\{40\}')
CODE=$(ls ../agenthk-${SHA:0:7}*.zip 2>/dev/null | head -1)
[ -n "$CODE" ] || { echo "Put the code zip (GitHub 'Download ZIP' of commit ${SHA:0:7}) in the installer folder first."; exit 1; }
unzip -l "$CODE" | grep -q "agenthk-$SHA/" || { echo "$CODE is not commit ${SHA:0:7}. Download the ZIP from that commit, not from main."; exit 1; }
STAGE="$(mktemp -d)"; K="$STAGE/Shyft-Tester-Windows"; mkdir -p "$K/files"
cp *.bat "READ ME FIRST.txt" "$K/"
cp common.ps1 results.ps1 install.ps1 run_test.ps1 remove.ps1 shyft.ico ../shyft_synthetic_set.zip "$CODE" "$K/files/"
# Shyft's screens, from the repo's ui/ folder (shown after the test). Not the landing page, never run data.
UI=../../ui
[ -f "$UI/index.html" ] && [ -f "$UI/results.js" ] || { echo "ui/index.html or ui/results.js is missing: run this from the repo."; exit 1; }
# Packed as a zip so testers can't open a results-less copy by mistake: only Install unpacks it.
(cd "$UI" && zip -q "$K/files/shyft_ui.zip" index.html open_results.html styles.css trust.css screens.css light.css mode.js buddies.js copy.js trust.js flow.js review.js trust_app.js locked.js results.js themes.js setup.js sample_review.js)
rm -f Shyft-Tester-Windows.zip
(cd "$STAGE" && zip -qr - Shyft-Tester-Windows) > Shyft-Tester-Windows.zip
echo "Built: $(pwd)/Shyft-Tester-Windows.zip"
echo "Next: test it on a Windows PC, then attach it to the same GitHub release as the Mac DMG."
