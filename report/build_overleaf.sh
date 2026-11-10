#!/usr/bin/env bash
# Convert report/report.md into a LaTeX project for Overleaf (main.tex + figures), zipped.
# Usage (from the project root, environment icefal active): bash report/build_overleaf.sh <output folder>
# Then in Overleaf: New Project > Upload Project > report_overleaf.zip
set -euo pipefail
out="${1:?give an output folder}"
build="$out/report_overleaf"
rm -rf "$build" && mkdir -p "$build/figures"

cd "$(dirname "$0")"
pandoc report.md -s -o "$build/main.tex" \
    -V geometry:margin=2.5cm -V fontsize=11pt -V colorlinks=true -V header-includes='\usepackage{xurl}'

# Figures: copy those used by the report, and point to figures/ instead of ../figures/
grep -oE '\.\./figures/[^)]*\.(png|pdf)' report.md | sort -u | while read -r f; do cp "$f" "$build/figures/"; done
sed -i 's#\.\./figures/#figures/#g' "$build/main.tex"

# Characters that pdfLaTeX (Overleaf's default compiler) does not know
sed -i 's/×/$\\times$/g; s/≥/$\\geq$/g; s/≤/$\\leq$/g; s/²/\\textsuperscript{2}/g' "$build/main.tex"

python -c "import shutil, sys; shutil.make_archive(sys.argv[1], 'zip', sys.argv[2])" "$out/report_overleaf" "$build"
echo "Written $out/report_overleaf.zip"
