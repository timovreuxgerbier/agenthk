#!/bin/bash
# make_dmg.sh — run ON A MAC to build Shyft-Tester.dmg (about 10 seconds; uses macOS's built-in hdiutil).
# Before running: put shyft_synthetic_set.zip (from Sphinx) and the code zip agenthk-524117b...zip (GitHub
# "Download ZIP" of the pinned commit, the same file the Windows kit uses) in this folder. Neither goes into Git.
# Run it with:   bash installer/make_dmg.sh
set -e
cd "$(dirname "$0")"
[ "$(uname)" = "Darwin" ] || { echo "Run this on a Mac (it needs hdiutil)."; exit 1; }
[ -f shyft_synthetic_set.zip ] || { echo "Put shyft_synthetic_set.zip in the installer folder first."; exit 1; }
SHA=$(grep -o 'CODE_COMMIT="[0-9a-f]*"' shyft_common.sh | grep -o '[0-9a-f]\{40\}')
CODE=$(ls agenthk-$(echo "$SHA" | cut -c1-7)*.zip 2>/dev/null | head -1)
[ -n "$CODE" ] || { echo "Put the code zip (GitHub 'Download ZIP' of commit $(echo "$SHA" | cut -c1-7)) in the installer folder first."; exit 1; }
unzip -l "$CODE" | grep -q "agenthk-$SHA/" || { echo "$CODE is not commit $(echo "$SHA" | cut -c1-7). Download the ZIP from that commit, not from main."; exit 1; }

STAGE="$(mktemp -d)/Shyft"; mkdir -p "$STAGE"
cp "READ ME FIRST.md"               "$STAGE/READ ME FIRST.md"
cp "Install Shyft.command"          "$STAGE/1 Install Shyft.command"     # numbers keep Finder in order
cp "Run the Shyft test.command"     "$STAGE/2 Run the Shyft test.command"
cp "Remove Shyft.command"           "$STAGE/3 Remove Shyft (when you're done).command"
cp shyft_common.sh shyft_synthetic_set.zip "$CODE" "$STAGE/"
chmod +x "$STAGE"/*.command

rm -f Shyft-Tester.dmg
hdiutil create -volname "Shyft" -srcfolder "$STAGE" -format UDZO -ov Shyft-Tester.dmg
echo
echo "Built: $(pwd)/Shyft-Tester.dmg"
echo "Next: open it yourself and test it, then attach it to a GitHub release (see installer/README.md)."
