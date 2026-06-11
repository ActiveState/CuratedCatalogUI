#!/usr/bin/env python3
"""Write scan_requirements.txt from data.json.

Usage:
  python3 prepare_scan.py         # 20 popular packages
  python3 prepare_scan.py --all   # all packages in the catalog
"""

import json
import sys

ALL_MODE = "--all" in sys.argv

POPULAR = [
    "requests", "urllib3", "flask", "django", "numpy", "pandas", "fastapi",
    "sqlalchemy", "pydantic", "boto3", "celery", "redis", "cryptography",
    "pillow", "paramiko", "aiohttp", "httpx", "uvicorn", "pytest", "click",
]

import os
_catalog = os.path.join(os.path.dirname(__file__), "..", "public", "data", "python", "catalog.json")
with open(_catalog) as f:
    packages = json.load(f)["packages"]

if ALL_MODE:
    candidates = [(p["name"], p["versions"]) for p in packages if p["versions"]]
else:
    catalog = {p["name"].lower(): p for p in packages}
    candidates = []
    skipped = []
    for pkg in POPULAR:
        entry = catalog.get(pkg)
        if not entry or not entry["versions"]:
            skipped.append(pkg)
        else:
            candidates.append((entry["name"], entry["versions"]))
    if skipped:
        print(f"Skipped (not in catalog): {', '.join(skipped)}")

lines = [f"{name}=={versions[-1]}" for name, versions in candidates]

with open("scan_requirements.txt", "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"scan_requirements.txt: {len(lines)} packages {'(full catalog)' if ALL_MODE else '(popular sample)'}")
