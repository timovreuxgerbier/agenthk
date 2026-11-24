#!/bin/bash
# make_windows_kit.sh - builds Shyft-Tester-Windows.zip. Works on a Mac or Linux (needs zip).
# Before running: put shyft_synthetic_set.zip (from Sphinx) in installer/ (Git ignores it).
# Run it with:   bash installer/windows/make_windows_kit.sh
set -e
cd "$(dirname "$0")"
[ -f ../shyft_synthetic_set.zip ] || { echo "Put shyft_synthetic_set.zip in the installer folder first."; exit 1; }
STAGE="$(mktemp -d)"; K="$STAGE/Shyft-Tester-Windows"; mkdir -p "$K/files"
cp *.bat "READ ME FIRST.txt" "$K/"
cp common.ps1 install.ps1 run_test.ps1 remove.ps1 ../shyft_synthetic_set.zip "$K/files/"
rm -f Shyft-Tester-Windows.zip
(cd "$STAGE" && zip -qr - Shyft-Tester-Windows) > Shyft-Tester-Windows.zip
echo "Built: $(pwd)/Shyft-Tester-Windows.zip"
echo "Next: test it on a Windows PC, then attach it to the same GitHub release as the Mac DMG."
