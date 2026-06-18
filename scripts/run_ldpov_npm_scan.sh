#!/usr/bin/env bash
# Run a CVE scan on the LDPoV npm catalog using osv-scanner (via Docker).
#
# Prerequisites:
#   - Docker
#   - public/data/ldpov/javascript/catalog.json exists (run fetch_ldpov_npm.py first)
#
# Writes: public/data/ldpov/javascript/audit.json
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

CATALOG="$DIR/../public/data/ldpov/javascript/catalog.json"
RESULTS="$DIR/results/ldpov-npm"
LOCKFILE="$RESULTS/package-lock.json"
OSV_RAW="$RESULTS/osv_raw.json"
OSV_IMAGE="ghcr.io/google/osv-scanner:latest"

if [ ! -f "$CATALOG" ]; then
  echo "ERROR: $CATALOG not found. Run fetch_ldpov_npm.py first." >&2
  exit 1
fi

mkdir -p "$RESULTS"

# ── Step 1: generate a v1 npm package-lock.json from the catalog ──────────────
echo "==> [1/3] Generating package-lock.json from catalog..."
python3 << PYEOF
import json

with open('$CATALOG') as f:
    pkgs = json.load(f)['packages']

deps = {}
for p in pkgs:
    if p['versions']:
        deps[p['name']] = {
            'version':   p['versions'][-1],
            'resolved':  '',
            'integrity': '',
        }

lock = {
    'name':            'ldpov-npm-scan',
    'version':         '1.0.0',
    'lockfileVersion': 1,
    'requires':        True,
    'dependencies':    deps,
}

with open('$LOCKFILE', 'w') as f:
    json.dump(lock, f)

print(f"  {len(deps)} packages written to lockfile")
PYEOF

# ── Step 2: run osv-scanner in Docker ─────────────────────────────────────────
echo ""
echo "==> [2/3] Running osv-scanner in Docker..."
echo "    Pulling $OSV_IMAGE if needed..."

docker run --rm --network host \
  -v "$RESULTS:/scan:ro" \
  "$OSV_IMAGE" \
  --lockfile /scan/package-lock.json \
  --format json \
  > "$OSV_RAW" || true

if [ ! -s "$OSV_RAW" ]; then
  echo "WARNING: osv-scanner produced no output. Writing empty result." >&2
  echo '{}' > "$OSV_RAW"
fi

# ── Step 3: normalize into audit.json shape ───────────────────────────────────
echo ""
echo "==> [3/3] Normalizing results..."
CUSTOMER=ldpov LANG_ID=javascript python3 normalize_npm_audit.py

echo ""
echo "Done. public/data/ldpov/javascript/audit.json updated."
