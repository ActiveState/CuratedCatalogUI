#!/usr/bin/env python3
"""Fetch all package names + versions from the LDPoV npm catalog.

Reads LDPOV_ORG_ID, LDPOV_CATALOG_TOKEN, NPM_URL from ../.env or environment.
Uses S3 redirect_map for package discovery, then fetches versions from the registry.
Writes public/data/ldpov/javascript/catalog.json.
"""

import datetime
import json
import os
import re
import subprocess
import urllib.parse
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

_env: dict[str, str] = {}
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    for line in open(_env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            _env[k.strip()] = v.strip()

ORG_ID  = os.environ.get("LDPOV_ORG_ID",          _env.get("LDPOV_ORG_ID",          ""))
TOKEN   = os.environ.get("LDPOV_CATALOG_TOKEN",    _env.get("LDPOV_CATALOG_TOKEN",    ""))
BASE_URL = os.environ.get("NPM_URL",               _env.get("NPM_URL",               ""))

if not ORG_ID or not TOKEN:
    raise SystemExit("ERROR: set LDPOV_ORG_ID and LDPOV_CATALOG_TOKEN in .env or environment")
if not BASE_URL:
    raise SystemExit("ERROR: set NPM_URL in .env or environment")

AUTH = b64encode(f"x:{TOKEN}".encode()).decode()


def get_package_list() -> list[str]:
    s3_path = f"s3://curated-catalog/env=prod/org-id={ORG_ID}/repo-type=npm/redirect_map.json"
    print(f"Fetching npm package list from S3: {s3_path}", flush=True)
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
    base = v.split("-")[0]
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
            if versions:
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
        os.path.dirname(__file__), "..", "public", "data", "ldpov", "javascript", "catalog.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    print(f"Wrote public/data/ldpov/javascript/catalog.json — {len(results)} packages ({total - len(results)} skipped, no versions)")


if __name__ == "__main__":
    main()
