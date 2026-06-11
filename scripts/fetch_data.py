#!/usr/bin/env python3
"""Fetch all package names + versions from the Curated Catalog and write a self-contained index.html."""

import base64
import datetime
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.parse import urljoin

# Load credentials and index ID from .env or environment variables
import os
_env = {}
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    for line in open(_env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            _env[k.strip()] = v.strip()

USER     = os.environ.get("CATALOG_USER",     _env.get("CATALOG_USER",     ""))
PASSWORD = os.environ.get("CATALOG_TOKEN",    _env.get("CATALOG_TOKEN",    ""))
INDEX_ID = os.environ.get("CATALOG_INDEX_ID", _env.get("CATALOG_INDEX_ID", ""))

if not USER or not PASSWORD:
    raise SystemExit("ERROR: set CATALOG_USER and CATALOG_TOKEN in .env or environment")
if not INDEX_ID:
    raise SystemExit("ERROR: set CATALOG_INDEX_ID in .env or environment")

BASE_URL = f"https://repo.activestate.com/{INDEX_ID}/pypi/simple/"
AUTH = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()

HREF_RE = re.compile(r'href="([^"]+)"')
WHL_VERSION_RE = re.compile(r'^[^-]+-([^-]+)-')

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Curated Catalog — Package Index</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      min-height: 100vh;
    }
    header {
      background: #1a1d27;
      border-bottom: 1px solid #2d3148;
      padding: 20px 32px;
      display: flex;
      align-items: center;
      gap: 16px;
    }
    header h1 { font-size: 1.4rem; font-weight: 600; color: #a78bfa; letter-spacing: -0.02em; }
    header .subtitle { font-size: 0.8rem; color: #64748b; margin-top: 2px; }
    .badge {
      background: #2d1e6e; color: #a78bfa; font-size: 0.72rem; font-weight: 600;
      padding: 3px 10px; border-radius: 20px; border: 1px solid #4c3799; margin-left: auto;
    }
    .toolbar {
      padding: 16px 32px; display: flex; gap: 12px; align-items: center;
      background: #13161f; border-bottom: 1px solid #1e2133; flex-wrap: wrap;
    }
    .search-wrap { position: relative; flex: 1; min-width: 200px; max-width: 480px; }
    .search-wrap svg {
      position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
      color: #475569; pointer-events: none;
    }
    #search {
      width: 100%; padding: 9px 12px 9px 38px; background: #1e2235;
      border: 1px solid #2d3556; border-radius: 8px; color: #e2e8f0;
      font-size: 0.88rem; outline: none; transition: border-color 0.15s;
    }
    #search:focus { border-color: #7c3aed; }
    #search::placeholder { color: #475569; }
    .count { font-size: 0.82rem; color: #64748b; white-space: nowrap; }
    .count span { color: #94a3b8; font-weight: 600; }
    .generated { font-size: 0.78rem; color: #3d4466; margin-left: auto; }
    .table-wrap { padding: 0 32px 40px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 0.875rem; }
    thead th {
      text-align: left; padding: 10px 16px; background: #1a1d27; color: #64748b;
      font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;
      border-bottom: 1px solid #2d3148; cursor: pointer; user-select: none; white-space: nowrap;
    }
    thead th:hover { color: #94a3b8; }
    thead th.sorted { color: #a78bfa; }
    thead th .sort-arrow { display: inline-block; margin-left: 4px; opacity: 0.5; font-size: 0.7rem; }
    thead th.sorted .sort-arrow { opacity: 1; }
    tbody tr { border-bottom: 1px solid #1a1d2b; transition: background 0.1s; }
    tbody tr:hover { background: #181b2a; }
    tbody td { padding: 11px 16px; vertical-align: middle; }
    td.pkg-name {
      font-family: "SF Mono", "Fira Code", "Cascadia Code", monospace;
      font-size: 0.82rem; color: #c4b5fd; white-space: nowrap;
    }
    td.pkg-name a { color: inherit; text-decoration: none; }
    td.pkg-name a:hover { text-decoration: underline; color: #a78bfa; }
    td.versions { color: #94a3b8; line-height: 1.7; }
    .version-pill {
      display: inline-block; background: #1e2235; border: 1px solid #2d3556;
      color: #7dd3fc; font-family: "SF Mono", "Fira Code", monospace; font-size: 0.72rem;
      padding: 1px 8px; border-radius: 4px; margin: 2px 3px 2px 0; white-space: nowrap;
    }
    .version-pill.latest { background: #1a2e1a; border-color: #2d5a2d; color: #86efac; }
    .no-version { color: #3d4466; font-style: italic; font-size: 0.78rem; }
    .td-index { color: #3d4466; font-size: 0.78rem; }
    #empty-state { text-align: center; padding: 80px 32px; color: #3d4466; display: none; }
    #empty-state h2 { font-size: 1.1rem; margin-bottom: 8px; color: #475569; }
    @media (max-width: 640px) {
      header, .toolbar, .table-wrap { padding-left: 16px; padding-right: 16px; }
    }
  </style>
</head>
<body>
<header>
  <div>
    <h1>Curated Catalog</h1>
    <div class="subtitle">ActiveState Package Index</div>
  </div>
  <span class="badge" id="total-badge">__TOTAL__ packages</span>
</header>
<div class="toolbar">
  <div class="search-wrap">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
    </svg>
    <input id="search" type="text" placeholder="Search packages…" autocomplete="off">
  </div>
  <div class="count">Showing <span id="shown-count">__TOTAL__</span> of <span id="total-count">__TOTAL__</span></div>
  <div class="generated" id="generated-ts">Updated __GENERATED__</div>
</div>
<div class="table-wrap">
  <table id="pkg-table">
    <thead>
      <tr>
        <th class="td-index" style="width:50px">#</th>
        <th data-col="name" class="sorted">Package <span class="sort-arrow">↑</span></th>
        <th data-col="count" style="width:80px">Count <span class="sort-arrow"></span></th>
        <th>Versions</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="empty-state">
    <h2>No packages found</h2>
    <p>Try a different search term.</p>
  </div>
</div>
<script>
const INDEX_URL = "__BASE_URL__";
const ALL_PACKAGES = __DATA__;

let sortCol = "name";
let sortDir = 1;

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function renderTable(packages) {
  const tbody = document.getElementById("tbody");
  const shownEl = document.getElementById("shown-count");
  const emptyEl = document.getElementById("empty-state");
  const tableEl = document.getElementById("pkg-table");

  if (packages.length === 0) {
    tableEl.style.display = "none";
    emptyEl.style.display = "block";
    shownEl.textContent = "0";
    return;
  }
  emptyEl.style.display = "none";
  tableEl.style.display = "table";
  shownEl.textContent = packages.length.toLocaleString();

  tbody.innerHTML = packages.map((pkg, i) => {
    const pkgUrl = INDEX_URL + pkg.name + "/";
    const versionsHtml = pkg.versions.length === 0
      ? \'<span class="no-version">—</span>\'
      : pkg.versions.map((v, vi) => {
          const isLatest = vi === pkg.versions.length - 1;
          return \'<span class="version-pill\' + (isLatest ? " latest" : "") + \'">\' + escHtml(v) + \'</span>\';
        }).join("");
    return \'<tr><td class="td-index">\' + (i+1) + \'</td><td class="pkg-name"><a href="\' + pkgUrl + \'" target="_blank" rel="noopener">\' + escHtml(pkg.name) + \'</a></td><td class="td-index" style="text-align:center">\' + pkg.versions.length + \'</td><td class="versions">\' + versionsHtml + \'</td></tr>\';
  }).join("");
}

function filterAndSort(query) {
  let result = ALL_PACKAGES;
  if (query) {
    const q = query.toLowerCase();
    result = result.filter(p => p.name.toLowerCase().includes(q));
  }
  result = [...result].sort((a, b) => {
    let av = sortCol === "name" ? a.name.toLowerCase() : a.versions.length;
    let bv = sortCol === "name" ? b.name.toLowerCase() : b.versions.length;
    return av < bv ? -sortDir : av > bv ? sortDir : 0;
  });
  renderTable(result);
}

document.querySelectorAll("thead th[data-col]").forEach(th => {
  th.addEventListener("click", () => {
    const col = th.dataset.col;
    sortDir = sortCol === col ? sortDir * -1 : 1;
    sortCol = col;
    document.querySelectorAll("thead th").forEach(t => {
      t.classList.remove("sorted");
      const a = t.querySelector(".sort-arrow");
      if (a) a.textContent = "";
    });
    th.classList.add("sorted");
    const a = th.querySelector(".sort-arrow");
    if (a) a.textContent = sortDir === 1 ? "↑" : "↓";
    filterAndSort(document.getElementById("search").value.trim());
  });
});

let searchTimer;
document.getElementById("search").addEventListener("input", e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => filterAndSort(e.target.value.trim()), 150);
});

filterAndSort("");
</script>
</body>
</html>'''


def get(url):
    req = Request(url, headers={"Authorization": f"Basic {AUTH}"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def fetch_versions(pkg_name):
    url = urljoin(BASE_URL, f"{pkg_name}/")
    try:
        html = get(url)
        versions = set()
        for href in HREF_RE.findall(html):
            filename = href.split("/")[-1]
            if filename.endswith(".whl"):
                m = WHL_VERSION_RE.match(filename)
                if m:
                    versions.add(m.group(1))
            elif filename.endswith(".tar.gz") or filename.endswith(".zip"):
                stem = filename.replace(".tar.gz", "").replace(".zip", "")
                parts = stem.rsplit("-", 1)
                if len(parts) == 2:
                    versions.add(parts[1])
        return pkg_name, sorted(versions, key=lambda v: [int(x) if x.isdigit() else x for x in re.split(r'[.\-]', v)])
    except Exception:
        return pkg_name, []


def main():
    print("Fetching package list...", flush=True)
    html = get(BASE_URL)
    packages = [m for m in HREF_RE.findall(html) if m.endswith("/")]
    packages = [p.rstrip("/") for p in packages]
    total = len(packages)
    print(f"Found {total} packages. Fetching versions...", flush=True)

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=30) as pool:
        futures = {pool.submit(fetch_versions, pkg): pkg for pkg in packages}
        for future in as_completed(futures):
            results.append(dict(zip(("name", "versions"), future.result())))
            done += 1
            if done % 100 == 0 or done == total:
                print(f"  {done}/{total}", flush=True)

    results.sort(key=lambda x: x["name"].lower())

    out = {
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "index_url": BASE_URL,
        "packages":  results,
    }

    out_path = os.path.join(os.path.dirname(__file__), "..", "public", "data", "python", "catalog.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    print(f"Wrote public/data/catalog.json — {total} packages, index: {INDEX_ID}")


if __name__ == "__main__":
    main()
