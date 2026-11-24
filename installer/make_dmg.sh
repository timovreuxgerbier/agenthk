#!/bin/bash
# make_dmg.sh — run ON A MAC to build Shyft-Tester.dmg (about 10 seconds; uses macOS's built-in hdiutil).
# Before running: put shyft_synthetic_set.zip (from Sphinx) in this folder. It's test data, so it isn't in Git.
# Run it with:   bash installer/make_dmg.sh
set -e
cd "$(dirname "$0")"
[ "$(uname)" = "Darwin" ] || { echo "Run this on a Mac (it needs hdiutil)."; exit 1; }
[ -f shyft_synthetic_set.zip ] || { echo "Put shyft_synthetic_set.zip in the installer folder first."; exit 1; }

STAGE="$(mktemp -d)/Shyft"; mkdir -p "$STAGE"
cp "READ ME FIRST.md"               "$STAGE/READ ME FIRST.md"
cp "Install Shyft.command"          "$STAGE/1 Install Shyft.command"     # numbers keep Finder in order
cp "Run the Shyft test.command"     "$STAGE/2 Run the Shyft test.command"
cp "Remove Shyft.command"           "$STAGE/3 Remove Shyft (when you're done).command"
cp shyft_common.sh shyft_synthetic_set.zip "$STAGE/"
chmod +x "$STAGE"/*.command

rm -f Shyft-Tester.dmg
hdiutil create -volname "Shyft" -srcfolder "$STAGE" -format UDZO -ov Shyft-Tester.dmg
echo
echo "Built: $(pwd)/Shyft-Tester.dmg"
echo "Next: open it yourself and test it, then attach it to a GitHub release (see installer/README.md)."
