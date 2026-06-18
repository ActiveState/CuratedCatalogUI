#!/usr/bin/env python3
"""Fetch all package names + versions from the LDPoV PyPI catalog.

Reads LDPOV_USER, LDPOV_CATALOG_TOKEN, PYPI_URL from ../.env or environment.
Writes public/data/ldpov/python/catalog.json.
"""

import base64
import datetime
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
from urllib.request import Request, urlopen

_env: dict[str, str] = {}
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    for line in open(_env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            _env[k.strip()] = v.strip()

USER     = os.environ.get("LDPOV_USER",           _env.get("LDPOV_USER",           ""))
PASSWORD = os.environ.get("LDPOV_CATALOG_TOKEN",  _env.get("LDPOV_CATALOG_TOKEN",  ""))
BASE_URL = os.environ.get("PYPI_URL",             _env.get("PYPI_URL",             ""))

if not USER or not PASSWORD:
    raise SystemExit("ERROR: set LDPOV_USER and LDPOV_CATALOG_TOKEN in .env or environment")
if not BASE_URL:
    raise SystemExit("ERROR: set PYPI_URL in .env or environment")

AUTH = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()

HREF_RE = re.compile(r'href="([^"]+)"')
WHL_VERSION_RE = re.compile(r'^[^-]+-([^-]+)-')


def get(url: str) -> str:
    req = Request(url, headers={"Authorization": f"Basic {AUTH}"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def fetch_versions(pkg_name: str) -> tuple[str, list[str]]:
    url = urljoin(BASE_URL, f"{pkg_name}/")
    try:
        html = get(url)
        versions: set[str] = set()
        for href in HREF_RE.findall(html):
            filename = href.split("/")[-1].split("#")[0]
            if filename.endswith(".whl"):
                m = WHL_VERSION_RE.match(filename)
                if m:
                    versions.add(m.group(1))
            elif filename.endswith(".tar.gz") or filename.endswith(".zip"):
                stem = filename.replace(".tar.gz", "").replace(".zip", "")
                parts = stem.rsplit("-", 1)
                if len(parts) == 2:
                    versions.add(parts[1])
        return pkg_name, sorted(
            versions,
            key=lambda v: [int(x) if x.isdigit() else x for x in re.split(r'[.\-]', v)],
        )
    except Exception:
        return pkg_name, []


def get_package_list_from_s3(org_id: str) -> list[str]:
    s3_path = f"s3://curated-catalog/env=prod/org-id={org_id}/repo-type=pypi/"
    print(f"Fetching PyPI package list from S3: {s3_path}", flush=True)
    result = subprocess.run(
        ["aws", "s3", "ls", s3_path],
        capture_output=True, text=True, check=True,
    )
    packages = []
    for line in result.stdout.splitlines():
        # Lines look like: "                           PRE numpy/"
        parts = line.strip().split()
        if len(parts) == 2 and parts[0] == "PRE":
            packages.append(parts[1].rstrip("/"))
    return sorted(packages, key=str.lower)


def main() -> None:
    org_id = os.environ.get("LDPOV_ORG_ID", _env.get("LDPOV_ORG_ID", ""))
    if not org_id:
        raise SystemExit("ERROR: set LDPOV_ORG_ID in .env or environment")

    packages = get_package_list_from_s3(org_id)
    total = len(packages)
    print(f"Found {total} packages. Fetching versions with 10 workers...", flush=True)

    results: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(fetch_versions, pkg): pkg for pkg in packages}
        for future in as_completed(futures):
            name, versions = future.result()
            if versions:
                results.append({"name": name, "versions": versions})
            done += 1
            if done % 100 == 0 or done == total:
                print(f"  {done}/{total}", flush=True)

    results.sort(key=lambda x: x["name"].lower())

    out = {
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "index_url": BASE_URL,
        "packages":  results,
    }

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "public", "data", "ldpov", "python", "catalog.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    print(f"Wrote public/data/ldpov/python/catalog.json — {len(results)} packages ({total - len(results)} skipped, no versions)")


if __name__ == "__main__":
    main()
