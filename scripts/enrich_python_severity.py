#!/usr/bin/env python3
"""Enrich the Python audit.json with severity data from the OSV API.

pip-audit does not include severity in its output. This script queries
https://api.osv.dev/v1/vulns/{id} for each vulnerability (preferring GHSA
aliases which have richer metadata) and writes the severity string back into
public/data/ldpov/python/audit.json.

Run after run_ldpov_pypi_scan.sh:
  python3 enrich_python_severity.py
"""

import json
import os
import time
import urllib.request

SCRIPT_DIR = os.path.dirname(__file__)
AUDIT_PATH = os.path.join(SCRIPT_DIR, "..", "public", "data", "ldpov", "python", "audit.json")


def fetch_severity(osv_id: str) -> str | None:
    url = f"https://api.osv.dev/v1/vulns/{osv_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            rec = json.loads(r.read())
        return (rec.get("database_specific") or {}).get("severity") or None
    except Exception:
        return None


def main() -> None:
    with open(AUDIT_PATH) as f:
        data = json.load(f)

    # Collect unique vulns that need enrichment
    vuln_lookup: dict[str, str] = {}  # audit_id -> best OSV id to query
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            if v.get("severity"):
                continue  # already enriched
            vid = v["id"]
            aliases = v.get("aliases", [])
            ghsa = next((a for a in aliases if a.startswith("GHSA-")), None)
            vuln_lookup[vid] = ghsa or vid

    if not vuln_lookup:
        print("All vulns already have severity. Nothing to do.")
        return

    print(f"Querying OSV API for {len(vuln_lookup)} vulns...", flush=True)

    severity_map: dict[str, str | None] = {}
    errors = 0
    for i, (audit_id, osv_id) in enumerate(vuln_lookup.items(), 1):
        sev = fetch_severity(osv_id)
        severity_map[audit_id] = sev
        if i % 20 == 0 or i == len(vuln_lookup):
            print(f"  {i}/{len(vuln_lookup)}", flush=True)
        time.sleep(0.05)

    # Patch in place
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            vid = v["id"]
            if vid in severity_map:
                v["severity"] = severity_map[vid]

    with open(AUDIT_PATH, "w") as f:
        json.dump(data, f, separators=(",", ":"))

    dist: dict[str, int] = {}
    for s in severity_map.values():
        dist[s or "unknown"] = dist.get(s or "unknown", 0) + 1
    print(f"Done. Severity distribution: {dist}")
    if errors:
        print(f"  {errors} OSV lookups failed (severity left as null)")


if __name__ == "__main__":
    main()
