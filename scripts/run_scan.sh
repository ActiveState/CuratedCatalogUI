#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Load credentials from ../.env or environment
ENV_FILE="$DIR/../.env"
if [ -f "$ENV_FILE" ]; then
  set -a; source "$ENV_FILE"; set +a
fi
if [ -z "${CATALOG_USER:-}" ] || [ -z "${CATALOG_TOKEN:-}" ] || [ -z "${CATALOG_INDEX_ID:-}" ]; then
  echo "ERROR: set CATALOG_USER, CATALOG_TOKEN, and CATALOG_INDEX_ID in .env or environment" >&2; exit 1
fi
INDEX_URL="https://${CATALOG_USER}:${CATALOG_TOKEN}@repo.activestate.com/${CATALOG_INDEX_ID}/pypi/simple/"

echo "==> [1/4] Preparing scan requirements..."
python3 prepare_scan.py "$@"

echo ""
echo "==> [2/4] Building Docker image..."
docker build -t curated-catalog-scan .

echo ""
echo "==> [3/4] Running CVE scan inside container..."
mkdir -p results
# All requirements are exactly pinned (package==x.y.z), so --disable-pip skips pip
# resolution entirely and checks directly against OSV — no index needed, no transitive deps.
# pip-audit exits 1 when vulnerabilities are found — that's expected, not a failure.
docker run --rm \
  -v "${DIR}/scan_requirements.txt:/scan/scan_requirements.txt:ro" \
  -v "${DIR}/results:/results" \
  curated-catalog-scan \
  sh -c 'pip-audit \
    -r /scan/scan_requirements.txt \
    --disable-pip \
    --no-deps \
    --format json \
    -o /results/audit.json; exit 0'

if [ ! -f "${DIR}/results/audit.json" ]; then
  echo "ERROR: audit.json was not created. Check Docker output above." >&2
  exit 1
fi

echo ""
echo "==> [4/4] Generating HTML report..."
python3 generate_report.py

echo ""
echo "Done. Open scan_report.html in your browser."
