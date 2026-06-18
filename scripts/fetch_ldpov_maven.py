#!/usr/bin/env python3
"""Fetch all artifact coordinates from the LDPoV Maven catalog.

Strategy (in order):
  1. Try S3 redirect_map: s3://curated-catalog/env=prod/org-id=<ID>/repo-type=maven2/redirect_map.json
  2. Fall back to crawling MAVEN_URL HTML index pages.

Reads LDPOV_ORG_ID, LDPOV_USER, LDPOV_CATALOG_TOKEN, MAVEN_URL from ../.env or environment.
Writes public/data/ldpov/java/catalog.json.

Output schema (same as Python/JS):
  { "generated": "...", "packages": [{"name": "group:artifact", "versions": ["1.0", ...]}, ...] }
"""

import base64
import datetime
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

_env: dict[str, str] = {}
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    for line in open(_env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            _env[k.strip()] = v.strip()

ORG_ID   = os.environ.get("LDPOV_ORG_ID",          _env.get("LDPOV_ORG_ID",          ""))
USER     = os.environ.get("LDPOV_USER",             _env.get("LDPOV_USER",             ""))
PASSWORD = os.environ.get("LDPOV_CATALOG_TOKEN",    _env.get("LDPOV_CATALOG_TOKEN",    ""))
BASE_URL = os.environ.get("MAVEN_URL",              _env.get("MAVEN_URL",              ""))

if not USER or not PASSWORD:
    raise SystemExit("ERROR: set LDPOV_USER and LDPOV_CATALOG_TOKEN in .env or environment")
if not BASE_URL:
    raise SystemExit("ERROR: set MAVEN_URL in .env or environment")

AUTH = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()


# ── Helpers ─────────────────────────────────────────────────────────────────

def http_get(url: str) -> str:
    req = Request(url, headers={"Authorization": f"Basic {AUTH}"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


class HrefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)


def list_dir(url: str) -> list[str]:
    """Return child hrefs from a Maven index HTML page."""
    try:
        html = http_get(url)
        p = HrefParser()
        p.feed(html)
        return [
            h for h in p.hrefs
            if not h.startswith("?") and not h.startswith("/") and h != "../"
        ]
    except Exception:
        return []


# ── Strategy 1: S3 redirect map ─────────────────────────────────────────────

def try_s3(org_id: str) -> list[dict] | None:
    s3_path = f"s3://curated-catalog/env=prod/org-id={org_id}/repo-type=maven2/redirect_map.json"
    print(f"Trying S3: {s3_path}", flush=True)
    try:
        result = subprocess.run(
            ["aws", "s3", "cp", s3_path, "-"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"  S3 not available (exit {result.returncode}), falling back to crawl.", flush=True)
            return None
        data: dict = json.loads(result.stdout)
    except Exception as e:
        print(f"  S3 error: {e}, falling back to crawl.", flush=True)
        return None

    # redirect_map keys are "group:artifact:version" triples
    # (plus some "group:artifact:maven-metadata.xml" markers to skip)
    coords: dict[str, set[str]] = {}
    for key in data:
        if key.endswith(":maven-metadata.xml"):
            continue
        if key.count(":") != 2:
            continue
        group_artifact, version = key.rsplit(":", 1)
        coords.setdefault(group_artifact, set()).add(version)

    packages = [
        {"name": coord, "versions": sorted(versions, key=_version_key)}
        for coord, versions in sorted(coords.items())
    ]
    if not packages:
        print("  S3 redirect_map exists but 0 Maven artifacts found; falling back to crawl.", flush=True)
        return None
    print(f"  S3 found {len(packages)} unique artifacts.", flush=True)
    return packages


# ── Strategy 2: crawl Maven index ───────────────────────────────────────────

def crawl_maven(base_url: str) -> list[dict]:
    print(f"Crawling Maven index at {base_url} ...", flush=True)

    # Level 1: group top-level dirs (e.g. "com/", "org/", "io/")
    top_dirs = [h for h in list_dir(base_url) if h.endswith("/") and h != "../"]
    print(f"  Top-level dirs: {len(top_dirs)}", flush=True)

    # Crawl up to depth 5 to find artifact dirs (dirs containing version subdirs
    # that contain .jar or .pom files).
    artifact_coords: dict[str, list[str]] = {}

    def crawl_dir(url: str, path_parts: list[str], depth: int) -> None:
        if depth > 6:
            return
        children = list_dir(url)
        subdirs  = [h for h in children if h.endswith("/") and h != "../"]
        files    = [h for h in children if not h.endswith("/")]

        # If this dir has version-like subdirs AND files like .pom/.jar, it's an artifact
        has_pom_jar = any(f.endswith(".pom") or f.endswith(".jar") for f in files)
        if has_pom_jar and len(path_parts) >= 2:
            artifact = path_parts[-1]
            group    = ".".join(path_parts[:-1])
            coord    = f"{group}:{artifact}"
            # Collect version subdirs from siblings (parent level)
            return  # versions are in subdirs of artifact dir; handled by caller

        for sub in subdirs:
            sub_name = sub.rstrip("/")
            sub_url  = urljoin(url, sub)
            sub_path = path_parts + [sub_name]

            # Detect artifact dir: it has subdirs that look like version numbers
            sub_children = list_dir(sub_url)
            sub_subdirs  = [h.rstrip("/") for h in sub_children if h.endswith("/") and h != "../"]
            sub_files    = [h for h in sub_children if not h.endswith("/")]

            looks_like_version = lambda s: bool(re.match(r'^[\d]', s))
            version_dirs = [s for s in sub_subdirs if looks_like_version(s)]

            if version_dirs:
                artifact = sub_name
                group    = ".".join(path_parts)
                coord    = f"{group}:{artifact}"
                if coord not in artifact_coords:
                    artifact_coords[coord] = sorted(version_dirs, key=_version_key)
            else:
                crawl_dir(sub_url, sub_path, depth + 1)

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [
            pool.submit(crawl_dir, urljoin(base_url, d), [d.rstrip("/")], 1)
            for d in top_dirs
        ]
        for f in as_completed(futures):
            pass  # errors silently ignored; best-effort crawl

    packages = [
        {"name": coord, "versions": versions}
        for coord, versions in sorted(artifact_coords.items())
    ]
    print(f"  Crawl found {len(packages)} artifacts.", flush=True)
    return packages


def _version_key(v: str) -> list:
    nums = re.findall(r"\d+", v.split("-")[0])
    return [int(n) for n in nums[:4]] + [0] * (4 - len(nums[:4]))


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    packages = try_s3(ORG_ID)
    if packages is None:
        packages = crawl_maven(BASE_URL)

    out = {
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "packages":  packages,
    }

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "public", "data", "ldpov", "java", "catalog.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    print(f"Wrote public/data/ldpov/java/catalog.json — {len(packages)} artifacts")


if __name__ == "__main__":
    main()
