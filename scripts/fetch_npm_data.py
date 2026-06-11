#!/usr/bin/env python3
"""Fetch all package names + versions from the npm Curated Catalog and write catalog.json.

Usage: python3 fetch_npm_data.py

Reads NPM_ORG_ID and NPM_BRIDGE_TOKEN from ../.env or environment.
Writes public/data/javascript/catalog.json.
"""

import base64
import datetime
import json
import os
import re
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

# Load .env
_env = {}
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    for line in open(_env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            _env[k.strip()] = v.strip()

ORG_ID       = os.environ.get("NPM_ORG_ID",      _env.get("NPM_ORG_ID",      ""))
BRIDGE_TOKEN = os.environ.get("NPM_BRIDGE_TOKEN", _env.get("NPM_BRIDGE_TOKEN", ""))

if not ORG_ID or not BRIDGE_TOKEN:
    raise SystemExit("ERROR: set NPM_ORG_ID and NPM_BRIDGE_TOKEN in .env or environment")

BASE_URL = f"https://repo.activestate.com/{ORG_ID}/npm/"
AUTH     = base64.b64encode(f"x:{BRIDGE_TOKEN}".encode()).decode()


def get_package_list() -> list[str]:
    """Fetch package names from the S3 redirect map."""
    s3_path = f"s3://curated-catalog/env=prod/org-id={ORG_ID}/repo-type=npm/redirect_map.json"
    print("Fetching package list from S3...", flush=True)
    result = subprocess.run(
        ["aws", "s3", "cp", s3_path, "-"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    names = sorted(
        {urllib.parse.unquote(k.split("/-/")[0]) for k in data},
        key=str.lower,
    )
    print(f"Found {len(names)} packages", flush=True)
    return names


def fetch_versions(name: str) -> tuple[str, list[str]]:
    """Fetch all available versions for a package from the registry packument."""
    # Scoped packages like @scope/name must encode the / as %2F in the URL path
    encoded = urllib.parse.quote(name, safe="@")
    url = f"{BASE_URL}{encoded}"
    try:
        req = Request(url, headers={"Authorization": f"Basic {AUTH}"})
        with urlopen(req, timeout=30) as r:
            doc = json.loads(r.read())
        versions = list(doc.get("versions", {}).keys())
        return name, sorted(versions, key=_version_key)
    except Exception:
        return name, []


def _version_key(v: str) -> list:
    """Sort semver strings numerically by major.minor.patch."""
    base = v.split("-")[0]  # strip pre-release suffix for ordering
    nums = re.findall(r"\d+", base)
    return [int(n) for n in nums[:3]] + [0] * (3 - len(nums[:3]))


def main() -> None:
    names = get_package_list()
    total = len(names)

    results: list[dict] = []
    done = 0
    print(f"Fetching versions with 30 workers...", flush=True)

    with ThreadPoolExecutor(max_workers=30) as pool:
        futures = {pool.submit(fetch_versions, n): n for n in names}
        for future in as_completed(futures):
            name, versions = future.result()
            results.append({"name": name, "versions": versions})
            done += 1
            if done % 500 == 0 or done == total:
                print(f"  {done}/{total}", flush=True)

    results.sort(key=lambda x: x["name"].lower())

    out = {
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "packages":  results,
    }

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "public", "data", "javascript", "catalog.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    print(f"Wrote public/data/javascript/catalog.json — {total} packages")


if __name__ == "__main__":
    main()
