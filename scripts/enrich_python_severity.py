#!/usr/bin/env python3
"""Enrich the Python audit.json with severity data from the OSV API.

pip-audit does not include severity in its output. This script queries
https://api.osv.dev/v1/vulns/{id} for each vulnerability (preferring GHSA
aliases which have richer metadata) and writes the severity string back into
public/data/ldpov/python/audit.json.

Severity resolution order:
  1. database_specific.severity  (GitHub advisory label — most entries)
  2. CVSS v3 base score derived from severity[].score vector string
  3. CVSS v4 key-metric heuristic (VC/VI/VA impact fields)

Run after run_ldpov_pypi_scan.sh:
  python3 enrich_python_severity.py
"""

import json
import math
import os
import re
import time
import urllib.request

SCRIPT_DIR = os.path.dirname(__file__)
AUDIT_PATH = os.path.join(SCRIPT_DIR, "..", "public", "data", "ldpov", "python", "audit.json")

# ── CVSS v3 base score ────────────────────────────────────────────────────────
_AV  = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
_AC  = {"L": 0.77, "H": 0.44}
_PR_U = {"N": 0.85, "L": 0.62, "H": 0.27}   # Scope Unchanged
_PR_C = {"N": 0.85, "L": 0.68, "H": 0.50}   # Scope Changed
_UI  = {"N": 0.85, "R": 0.62}
_CIA = {"N": 0.00, "L": 0.22, "H": 0.56}


def _roundup(x: float) -> float:
    return math.ceil(x * 10) / 10


def cvss3_score(vector: str) -> float | None:
    """Return CVSS v3 base score from a vector string, or None on parse error."""
    try:
        parts = dict(p.split(":") for p in vector.split("/")[1:])
        s = parts.get("S", "U")
        av = _AV[parts["AV"]]; ac = _AC[parts["AC"]]
        pr = (_PR_C if s == "C" else _PR_U)[parts["PR"]]
        ui = _UI[parts["UI"]]
        c = _CIA[parts["C"]]; i = _CIA[parts["I"]]; a = _CIA[parts["A"]]
        isc_base = 1 - (1 - c) * (1 - i) * (1 - a)
        if isc_base == 0:
            return 0.0
        if s == "U":
            isc = 6.42 * isc_base
        else:
            isc = 7.52 * (isc_base - 0.029) - 3.25 * (isc_base - 0.02) ** 15
        exp = 8.22 * av * ac * pr * ui
        if s == "U":
            return _roundup(min(isc + exp, 10))
        else:
            return _roundup(min(1.08 * (isc + exp), 10))
    except Exception:
        return None


def cvss4_heuristic(vector: str) -> str | None:
    """Estimate severity from CVSS v4 vector using VC/VI/VA impact fields."""
    try:
        parts = dict(p.split(":") for p in vector.split("/")[1:])
        impacts = [parts.get("VC", "N"), parts.get("VI", "N"), parts.get("VA", "N")]
        if "H" in impacts:
            return "HIGH"
        if impacts.count("L") >= 2:
            return "MODERATE"
        if "L" in impacts:
            return "LOW"
        return "LOW"
    except Exception:
        return None


def score_to_label(score: float) -> str:
    if score >= 9.0: return "CRITICAL"
    if score >= 7.0: return "HIGH"
    if score >= 4.0: return "MODERATE"
    return "LOW"


# ── OSV lookup ────────────────────────────────────────────────────────────────

def fetch_osv(osv_id: str) -> str | None:
    url = f"https://api.osv.dev/v1/vulns/{osv_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            rec = json.loads(r.read())

        # 1. database_specific label
        sev = (rec.get("database_specific") or {}).get("severity")
        if sev:
            return sev

        # 2. CVSS vector fallback
        for entry in rec.get("severity", []):
            vec = entry.get("score", "")
            t = entry.get("type", "")
            if t == "CVSS_V3" and vec.startswith("CVSS:3"):
                score = cvss3_score(vec)
                if score is not None:
                    return score_to_label(score)
            if t == "CVSS_V4" and vec.startswith("CVSS:4"):
                label = cvss4_heuristic(vec)
                if label:
                    return label

        return None
    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    with open(AUDIT_PATH) as f:
        data = json.load(f)

    vuln_lookup: dict[str, str] = {}
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            if v.get("severity"):
                continue
            vid = v["id"]
            aliases = v.get("aliases", [])
            ghsa = next((a for a in aliases if a.startswith("GHSA-")), None)
            vuln_lookup[vid] = ghsa or vid

    if not vuln_lookup:
        print("All vulns already have severity. Nothing to do.")
        return

    print(f"Querying OSV API for {len(vuln_lookup)} vulns...", flush=True)

    severity_map: dict[str, str | None] = {}
    for i, (audit_id, osv_id) in enumerate(vuln_lookup.items(), 1):
        severity_map[audit_id] = fetch_osv(osv_id)
        if i % 20 == 0 or i == len(vuln_lookup):
            print(f"  {i}/{len(vuln_lookup)}", flush=True)
        time.sleep(0.05)

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
    print(f"Done. Severity distribution for newly enriched: {dist}")


if __name__ == "__main__":
    main()
