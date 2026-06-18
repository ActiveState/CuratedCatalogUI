#!/usr/bin/env python3
"""Fetch all package names + versions from the LDPoV PyPI catalog.

Reads LDPOV_ORG_ID from ../.env or environment.
Fetches the redirect_map from S3 and extracts package names + versions
directly from the wheel/sdist filenames — no registry calls needed.
Writes public/data/ldpov/python/catalog.json.
"""

import datetime
import json
import os
import re
import subprocess
import urllib.parse
from collections import defaultdict

_env: dict[str, str] = {}
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    for line in open(_env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            _env[k.strip()] = v.strip()

ORG_ID = os.environ.get("LDPOV_ORG_ID", _env.get("LDPOV_ORG_ID", ""))

if not ORG_ID:
    raise SystemExit("ERROR: set LDPOV_ORG_ID in .env or environment")

# wheel filename: {distribution}-{version}(-{build})?-{python}-{abi}-{platform}.whl
_WHL_RE = re.compile(r'^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)-(\d[^-]*)(-.*)?\.whl$')
# sdist filename: {distribution}-{version}.tar.gz or .zip
_SDIST_RE = re.compile(r'^(.+?)-(\d[\w.\-+]*)\.(?:tar\.gz|zip)$')


def _normalize(name: str) -> str:
    return re.sub(r'[-_.]+', '-', name).lower()


def _version_key(v: str) -> list:
    return [int(x) if x.isdigit() else x for x in re.split(r'[.\-]', v.split('+')[0])]


def main() -> None:
    s3_path = f"s3://curated-catalog/env=prod/org-id={ORG_ID}/repo-type=pypi/redirect_map.json"
    print(f"Fetching PyPI redirect_map from S3: {s3_path}", flush=True)
    result = subprocess.run(
        ["aws", "s3", "cp", s3_path, "-"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    print(f"Found {len(data)} redirect entries", flush=True)

    pkg_versions: dict[str, set[str]] = defaultdict(set)
    for raw_key in data:
        # keys are: {sha256_hash}/{filename}
        parts = raw_key.split('/', 1)
        if len(parts) != 2:
            continue
        filename = urllib.parse.unquote(parts[1])

        m = _WHL_RE.match(filename)
        if m:
            dist    = _normalize(m.group(1))
            version = m.group(3)
            pkg_versions[dist].add(version)
            continue

        m = _SDIST_RE.match(filename)
        if m:
            dist    = _normalize(m.group(1))
            version = m.group(2)
            pkg_versions[dist].add(version)

    packages = [
        {"name": name, "versions": sorted(versions, key=_version_key)}
        for name, versions in sorted(pkg_versions.items(), key=lambda x: x[0].lower())
    ]

    out = {
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "packages":  packages,
    }

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "public", "data", "ldpov", "python", "catalog.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    print(f"Wrote public/data/ldpov/python/catalog.json — {len(packages)} packages")


if __name__ == "__main__":
    main()
