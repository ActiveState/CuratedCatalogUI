#!/usr/bin/env python3
"""Normalize osv-scanner JSON output into the audit.json shape the frontend expects.

Reads:
  results/npm/osv_raw.json   — osv-scanner --format json output
  public/data/javascript/catalog.json — to include clean packages in the output

Writes:
  public/data/javascript/audit.json
"""

import json
import os

DIR      = os.path.dirname(__file__)
CUSTOMER = os.environ.get("CUSTOMER", "aspov")
LANG     = os.environ.get("LANG_ID",  os.environ.get("LANG", "javascript"))

_results_subdir = "npm" if CUSTOMER == "aspov" else f"{CUSTOMER}-npm"
OSV_RAW  = os.path.join(DIR, "results", _results_subdir, "osv_raw.json")
CATALOG  = os.path.join(DIR, "..", "public", "data", CUSTOMER, LANG, "catalog.json")
OUT_PATH = os.path.join(DIR, "..", "public", "data", CUSTOMER, LANG, "audit.json")


def extract_fix_versions(vuln: dict) -> list[str]:
    """Pull fixed-version strings out of the OSV affected[].ranges[].events list."""
    fixes = set()
    for affected in vuln.get("affected", []):
        for r in affected.get("ranges", []):
            if r.get("type") in ("ECOSYSTEM", "SEMVER"):
                for event in r.get("events", []):
                    if "fixed" in event:
                        fixes.add(event["fixed"])
    return sorted(fixes)


def main() -> None:
    # Load catalog for the full package list (name → latest version)
    with open(CATALOG) as f:
        catalog = json.load(f)
    pkg_versions = {
        p["name"]: p["versions"][-1]
        for p in catalog["packages"]
        if p["versions"]
    }

    # Load osv-scanner output; it may be empty or contain {"results": []}
    vuln_map: dict[str, list[dict]] = {}  # package name → list of vulns
    if os.path.exists(OSV_RAW) and os.path.getsize(OSV_RAW) > 0:
        with open(OSV_RAW) as f:
            raw = f.read().strip()

        # osv-scanner may mix human-readable progress lines with JSON when piped;
        # find the first '{' to isolate the JSON object.
        json_start = raw.find("{")
        if json_start >= 0:
            osv_data = json.loads(raw[json_start:])
        else:
            osv_data = {}

        seen: set[tuple] = set()  # (name, vuln_id) dedup guard

        for result in osv_data.get("results", []):
            for pkg_entry in result.get("packages", []):
                name    = pkg_entry["package"]["name"]
                for vuln in pkg_entry.get("vulnerabilities", []):
                    vuln_id = vuln.get("id", "")
                    key = (name, vuln_id)
                    if key in seen:
                        continue
                    seen.add(key)

                    aliases      = vuln.get("aliases", [])
                    description  = vuln.get("details", "") or vuln.get("summary", "")
                    fix_versions = extract_fix_versions(vuln)
                    severity     = (vuln.get("database_specific") or {}).get("severity") or None

                    vuln_map.setdefault(name, []).append({
                        "id":           vuln_id,
                        "aliases":      aliases,
                        "fix_versions": fix_versions,
                        "description":  description,
                        "severity":     severity,
                    })

    # Build dependencies list: every scanned package, clean or vulnerable
    dependencies = []
    for name, version in sorted(pkg_versions.items(), key=lambda x: x[0].lower()):
        dependencies.append({
            "name":    name,
            "version": version,
            "vulns":   vuln_map.get(name, []),
        })

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({"dependencies": dependencies}, f, separators=(",", ":"))

    total_vuln = sum(1 for d in dependencies if d["vulns"])
    total_cves = sum(len(d["vulns"]) for d in dependencies)
    print(
        f"Wrote public/data/{CUSTOMER}/{LANG}/audit.json — "
        f"{len(dependencies)} packages, {total_vuln} vulnerable, {total_cves} findings"
    )


if __name__ == "__main__":
    main()
