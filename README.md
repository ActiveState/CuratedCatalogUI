# CuratedCatalog UI

A demo interface for the ActiveState Curated Catalog — a curated, vetted package index covering multiple languages. Built for customer POVs and sales demos.

Live: **https://activestate.github.io/CuratedCatalogUI/**

---

## What this is

The ActiveState Curated Catalog provides private, security-vetted package indexes. This UI gives customers a visual overview of catalog contents and security posture across languages — things that are otherwise invisible when consuming the index via a package manager.

Languages currently live: **Python**, **JavaScript**. Java, Go, Rust, PHP, C#/.NET, R, and C/C++ are shown in the navbar as coming soon.

### Catalog browser (`/:lang`)

Full package table with inline information — no need to click into individual packages:

- **Package name** — monospace, truncates gracefully on very long names
- **Versions** — all version pills in the row, latest highlighted; column is fixed-width so layout is consistent across languages
- **Vulnerabilities Summary** — CVE alias or vuln ID pill per vulnerability (`CVE-…`, `PYSEC-…`, `GHSA-…`), or a green **Clean** badge if none. Sortable — click to put vulnerable packages first.
- **View ↗** *(Python only)* — direct link to the package's page in the private PyPI index

Live search + sortable columns (name, CVE status).

### CVE scan report (`/:lang/cve-report`)

Opens on the **Vulnerable** filter by default.

- **Stat cards** — packages scanned / vulnerable / total CVEs / clean / scanner tool
- **Filter** — All / Vulnerable / Clean
- **Per-row** — version pill, vuln ID, CVE aliases, fix version, truncated description
- **Description modal** — click `ⓘ` for the full description rendered as formatted text: headers, bold, inline code, code blocks, bullet lists, and clickable links. Multi-CVE packages let you switch between vulnerabilities inside the modal.
- **Unaudited notice** *(JavaScript)* — packages with no published registry versions are excluded from the scan; a banner shows the count with a toggle to browse the full list.

**Python** — scanned with `pip-audit` + OSV inside Docker (`--disable-pip --no-deps`).  
**JavaScript** — scanned with `osv-scanner` via Docker against a generated `package-lock.json`.

---

## Tech stack

- **React 18 + TypeScript + Vite**
- **React Router v6** (HashRouter — works on GitHub Pages without server config)
- **CSS variables** — light and dark themes matching the ActiveState design system
- **GitHub Actions** — `vite build` → deploys to `gh-pages` branch on every push to `main`

---

## Repo structure

```
├── public/data/
│   ├── python/
│   │   ├── catalog.json      Python package list + versions (refreshed manually)
│   │   └── audit.json        pip-audit CVE results (refreshed manually)
│   └── javascript/
│       ├── catalog.json      npm package list + versions (refreshed manually)
│       └── audit.json        osv-scanner CVE results (refreshed manually)
├── src/
│   ├── languages.ts          Language registry (id, label, icon, scanTool, disabled)
│   ├── hooks/
│   │   └── useLanguageData.ts  Fetches + caches catalog.json + audit.json per language
│   ├── components/           Navbar, VersionPill, CvePill, StatCard, DescriptionCell
│   ├── context/              DataContext (legacy; superseded by useLanguageData)
│   ├── pages/                CatalogPage, ScanReportPage, PackageDetailPage
│   └── styles/               CSS variables (tokens.css) + global base styles
├── scripts/                  Data pipelines (Python + Docker)
└── .github/workflows/        CI deploy to GitHub Pages
```

---

## Environment setup

Copy `.env.example` to `.env` and fill in your values:

```
CATALOG_USER=your_user_here
CATALOG_TOKEN=<your token>
CATALOG_INDEX_ID=<python index UUID>
NPM_ORG_ID=<npm org id>
NPM_BRIDGE_TOKEN=<npm bridge token>
```

`.env` is gitignored — never commit real credentials.

---

## Refreshing data

### Python

```bash
cd scripts
python3 fetch_data.py         # → ../public/data/python/catalog.json
bash run_scan.sh --all        # → ../public/data/python/audit.json
cd ..
git add public/data/python/
git commit -m "chore: refresh Python catalog + CVE data"
git push
```

Fetch ~5 min (1700+ packages, 30 concurrent requests). Scan ~5 min (OSV lookup via Docker, no installs).

### JavaScript

```bash
# Requires: AWS CLI logged in (aws sso login), Docker running
cd scripts
python3 fetch_npm_data.py     # → ../public/data/javascript/catalog.json
bash run_npm_scan.sh          # → ../public/data/javascript/audit.json
cd ..
git add public/data/javascript/
git commit -m "chore: refresh JavaScript catalog + CVE data"
git push
```

Fetch ~10 min (4000+ packages, 30 concurrent requests). Scan uses `ghcr.io/google/osv-scanner` via Docker.

---

## Local development

```bash
npm install
npm run dev       # http://localhost:5173/CuratedCatalogUI/
```

Navigate to `/python` or `/javascript` (the root redirects to `/python` by default).

---

## Scripts (`scripts/`)

| File | Language | Purpose |
|---|---|---|
| `fetch_data.py` | Python | Fetch packages + versions from private PyPI → `public/data/python/catalog.json` |
| `prepare_scan.py` | Python | Build `scan_requirements.txt` for pip-audit |
| `run_scan.sh` | Python | Run pip-audit in Docker → `public/data/python/audit.json` |
| `fetch_npm_data.py` | JavaScript | Fetch package list from S3 + versions from npm registry → `public/data/javascript/catalog.json` |
| `run_npm_scan.sh` | JavaScript | Run osv-scanner in Docker → `public/data/javascript/audit.json` |
| `normalize_npm_audit.py` | JavaScript | Normalize osv-scanner JSON into the shared audit.json schema |
| `Dockerfile` | Python | `python:3.12-slim` + `pip-audit` for Python scanning |

---

## Adding a new language

1. Add an entry to `src/languages.ts` (set `disabled: true` until data is ready).
2. Create `public/data/<lang>/catalog.json` and `audit.json` matching the existing schema.
3. Add fetch + scan scripts under `scripts/`.
4. Remove `disabled: true` from the language entry to make it live.

