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


def main() -> None:
    print("Fetching LDPoV PyPI package list...", flush=True)
    html = get(BASE_URL)
    packages = [m.rstrip("/") for m in HREF_RE.findall(html) if m.endswith("/")]
    total = len(packages)
    print(f"Found {total} packages. Fetching versions with 30 workers...", flush=True)

    results: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=30) as pool:
        futures = {pool.submit(fetch_versions, pkg): pkg for pkg in packages}
        for future in as_completed(futures):
            name, versions = future.result()
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

    print(f"Wrote public/data/ldpov/python/catalog.json — {total} packages")


if __name__ == "__main__":
    main()
