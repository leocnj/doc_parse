#!/usr/bin/env bash
# Downloads the Molloy University Benefits Guides into this directory.
# Run from the repo root:  bash raw/download.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

URL_2024="https://www.molloy.edu/about/administration/human-resources/documents/molloy-university_benefit-guide_20240101-final.pdf"
URL_2025="https://www.molloy.edu/about/administration/human-resources/documents/1-molloy-university-2025-benefits-guide-11.13.2024-1.pdf"

echo "Downloading 2024 Benefits Guide..."
curl -L --progress-bar -o "$SCRIPT_DIR/molloy-univ-2024.pdf" "$URL_2024"

echo "Downloading 2025 Benefits Guide..."
curl -L --progress-bar -o "$SCRIPT_DIR/molloy-univ-2025.pdf" "$URL_2025"

echo ""
echo "Done. Files saved to raw/:"
ls -lh "$SCRIPT_DIR"/*.pdf
