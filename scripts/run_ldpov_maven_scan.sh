#!/usr/bin/env bash
# Run a CVE scan on the LDPoV Maven catalog using osv-scanner (via Docker).
#
# Prerequisites:
#   - Docker
#   - public/data/ldpov/java/catalog.json exists (run fetch_ldpov_maven.py first)
#
# Writes: public/data/ldpov/java/audit.json
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

CATALOG="$DIR/../public/data/ldpov/java/catalog.json"
RESULTS="$DIR/results/ldpov-java"
POM_FILE="$RESULTS/pom.xml"
OSV_RAW="$RESULTS/osv_raw.json"
OSV_IMAGE="ghcr.io/google/osv-scanner:latest"

if [ ! -f "$CATALOG" ]; then
  echo "ERROR: $CATALOG not found. Run fetch_ldpov_maven.py first." >&2
  exit 1
fi

mkdir -p "$RESULTS"

# ── Step 1: build a pom.xml from the catalog ──────────────────────────────────
echo "==> [1/3] Generating pom.xml from catalog..."
export CATALOG POM_FILE
python3 << 'PYEOF'
import json, os, sys

CATALOG = os.environ["CATALOG"]
POM_FILE = os.environ["POM_FILE"]

with open(CATALOG) as f:
    data = json.load(f)

deps_xml = []
for pkg in data["packages"]:
    name = pkg["name"]
    versions = pkg["versions"]
    if not versions:
        continue
    version = versions[-1]
    if ":" in name:
        group_id, artifact_id = name.split(":", 1)
    else:
        group_id = "unknown"
        artifact_id = name
    deps_xml.append(
        f"    <dependency>\n"
        f"      <groupId>{group_id}</groupId>\n"
        f"      <artifactId>{artifact_id}</artifactId>\n"
        f"      <version>{version}</version>\n"
        f"    </dependency>"
    )

pom = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>activestate.ldpov</groupId>
  <artifactId>ldpov-java-scan</artifactId>
  <version>1.0.0</version>
  <dependencies>
{chr(10).join(deps_xml)}
  </dependencies>
</project>
"""

with open(POM_FILE, "w") as f:
    f.write(pom)

print(f"  {len(deps_xml)} dependencies written to pom.xml")
PYEOF

# ── Step 2: run osv-scanner in Docker ─────────────────────────────────────────
echo ""
echo "==> [2/3] Running osv-scanner in Docker..."
echo "    Pulling $OSV_IMAGE if needed..."

docker run --rm --network host \
  -v "$RESULTS:/scan:ro" \
  "$OSV_IMAGE" \
  scan source \
  --lockfile /scan/pom.xml \
  --no-resolve \
  -f json \
  > "$OSV_RAW" || true

if [ ! -s "$OSV_RAW" ]; then
  echo "WARNING: osv-scanner produced no output. Writing empty result." >&2
  echo '{}' > "$OSV_RAW"
fi

# ── Step 3: normalize into audit.json ─────────────────────────────────────────
echo ""
echo "==> [3/3] Normalizing results..."
python3 normalize_maven_audit.py

echo ""
echo "Done. public/data/ldpov/java/audit.json updated."
