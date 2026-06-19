#!/usr/bin/env python3
"""Normalize osv-scanner JSON output for Maven into the shared audit.json shape.

Input:  scripts/results/ldpov-java/osv_raw.json   (osv-scanner --format json output)
        public/data/ldpov/java/catalog.json        (full package list)
Output: public/data/ldpov/java/audit.json

Output shape (matches Python/JS audit.json):
  [
    {
      "name": "group:artifact",
      "version": "1.2.3",
      "vulns": [
        {
          "id": "GHSA-xxxx",
          "aliases": ["CVE-2023-xxxx"],
          "fix_versions": ["1.2.4"],
          "description": "..."
        }
      ]
    },
    ...
  ]

All catalog packages are included (vulns: [] for clean ones) so the UI
counts them as scanned rather than unaudited.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(__file__)
RAW_PATH     = os.path.join(SCRIPT_DIR, "results", "ldpov-java", "osv_raw.json")
CATALOG_PATH = os.path.join(SCRIPT_DIR, "..", "public", "data", "ldpov", "java", "catalog.json")
OUT_PATH     = os.path.join(SCRIPT_DIR, "..", "public", "data", "ldpov", "java", "audit.json")


def main() -> None:
    if not os.path.exists(RAW_PATH):
        raise SystemExit(f"ERROR: {RAW_PATH} not found. Run run_ldpov_maven_scan.sh first.")
    if not os.path.exists(CATALOG_PATH):
        raise SystemExit(f"ERROR: {CATALOG_PATH} not found. Run fetch_ldpov_maven.py first.")

    with open(RAW_PATH) as f:
        raw = json.load(f)
    with open(CATALOG_PATH) as f:
        catalog = json.load(f)

    # Build vuln map from osv-scanner output: "name@version" -> [vulns]
    vuln_map: dict[str, list] = {}
    for result in raw.get("results", []):
        for pkg in result.get("packages", []):
            info    = pkg.get("package", {})
            name    = info.get("name", "")
            version = info.get("version", "")
            key     = f"{name}@{version}"

            if key not in vuln_map:
                vuln_map[key] = []

            for vuln in pkg.get("vulnerabilities", []):
                vid     = vuln.get("id", "")
                aliases = [a for a in vuln.get("aliases", []) if a.startswith("CVE-")]
                desc    = vuln.get("details", "") or vuln.get("summary", "")

                fix_versions: list[str] = []
                for affected in vuln.get("affected", []):
                    for rng in affected.get("ranges", []):
                        for event in rng.get("events", []):
                            if "fixed" in event:
                                fix_versions.append(event["fixed"])

                severity = (vuln.get("database_specific") or {}).get("severity") or None

                vuln_map[key].append({
                    "id":           vid,
                    "aliases":      aliases,
                    "fix_versions": sorted(set(fix_versions)),
                    "description":  desc,
                    "severity":     severity,
                })

    # Emit one entry per catalog package (latest version), overlaying vulns
    output = []
    for pkg in catalog.get("packages", []):
        name     = pkg.get("name", "")
        versions = pkg.get("versions", [])
        if not versions:
            continue
        version = versions[-1]
        key     = f"{name}@{version}"
        output.append({
            "name":    name,
            "version": version,
            "vulns":   vuln_map.get(key, []),
        })

    output.sort(key=lambda d: d["name"].lower())

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    vuln_count = sum(len(d["vulns"]) for d in output)
    vuln_pkgs  = sum(1 for d in output if d["vulns"])
    print(f"Wrote {OUT_PATH} — {len(output)} packages ({vuln_pkgs} vulnerable), {vuln_count} vulnerabilities")


if __name__ == "__main__":
    main()
