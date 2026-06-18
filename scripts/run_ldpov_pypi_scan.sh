#!/usr/bin/env bash
# Run a CVE scan on the LDPoV PyPI catalog using pip-audit (via Docker).
#
# Prerequisites:
#   - Docker
#   - public/data/ldpov/python/catalog.json exists (run fetch_ldpov_pypi.py first)
#
# Writes: public/data/ldpov/python/audit.json
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

ENV_FILE="$DIR/../.env"
if [ -f "$ENV_FILE" ]; then
  set -a; source "$ENV_FILE"; set +a
fi

if [ -z "${LDPOV_USER:-}" ] || [ -z "${LDPOV_CATALOG_TOKEN:-}" ] || [ -z "${PYPI_URL:-}" ]; then
  echo "ERROR: set LDPOV_USER, LDPOV_CATALOG_TOKEN, and PYPI_URL in .env or environment" >&2
  exit 1
fi

CATALOG="$DIR/../public/data/ldpov/python/catalog.json"
RESULTS="$DIR/results/ldpov-python"

if [ ! -f "$CATALOG" ]; then
  echo "ERROR: $CATALOG not found. Run fetch_ldpov_pypi.py first." >&2
  exit 1
fi

mkdir -p "$RESULTS"

# ── Step 1: build pinned requirements.txt from catalog ────────────────────────
echo "==> [1/4] Building scan_requirements.txt from catalog..."
python3 << PYEOF
import json

with open('$CATALOG') as f:
    data = json.load(f)

lines = []
for pkg in data['packages']:
    if pkg['versions']:
        lines.append(f"{pkg['name']}=={pkg['versions'][-1]}")

with open('$RESULTS/scan_requirements.txt', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"  {len(lines)} packages pinned")
PYEOF

# ── Step 2: build Docker image (reuse existing if present) ────────────────────
echo ""
echo "==> [2/4] Building Docker image..."
docker build --network host -t curated-catalog-scan "$DIR"

# ── Step 3: run pip-audit ──────────────────────────────────────────────────────
echo ""
echo "==> [3/4] Running CVE scan inside container..."
docker run --rm --network host \
  -v "${RESULTS}/scan_requirements.txt:/scan/scan_requirements.txt:ro" \
  -v "${RESULTS}:/results" \
  curated-catalog-scan \
  sh -c 'pip-audit \
    -r /scan/scan_requirements.txt \
    --disable-pip \
    --no-deps \
    --format json \
    -o /results/audit.json; exit 0'

if [ ! -f "${RESULTS}/audit.json" ]; then
  echo "ERROR: audit.json was not created. Check Docker output above." >&2
  exit 1
fi

# ── Step 4: copy to public/data ───────────────────────────────────────────────
echo ""
echo "==> [4/4] Copying audit.json to public/data/ldpov/python/..."
mkdir -p "$DIR/../public/data/ldpov/python"
cp "${RESULTS}/audit.json" "$DIR/../public/data/ldpov/python/audit.json"

echo ""
echo "Done. public/data/ldpov/python/audit.json updated."
