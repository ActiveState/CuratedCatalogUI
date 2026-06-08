# CuratedCatalog UI

A demo interface for the ActiveState Curated Catalog — a private PyPI index of curated, vetted Python packages. Built for customer POVs and sales demos.

Live: **https://activestate.github.io/CuratedCatalogUI/**

---

## What this is

The ActiveState Curated Catalog is a private PyPI-compatible package index. This UI gives customers a visual overview of the catalog's contents and security posture — two things that are otherwise invisible when using the index via `pip`.

### Catalog browser (`/`)

Browsable table of all packages in the index — name, available versions, and a direct link to each package's index page. Supports live search and column sorting. Data is refreshed manually by running the fetch script and pushing.

### CVE scan report (`/cve-report`)

The catalog is scanned against the [OSV advisory database](https://osv.dev/) using `pip-audit` running inside a Docker container. The report shows:

- Summary cards: packages scanned / vulnerable / total CVEs / clean
- Per-package CVE IDs, aliases, affected versions, and available fixes
- Filter by All / Vulnerable / Clean

The scanner uses `--disable-pip --no-deps` — it checks exact pinned versions against OSV without installing anything, so the scan is fast (~5 min for 1700+ packages).

---

## Tech stack

- **React 18 + TypeScript + Vite**
- **React Router v6** — catalog, CVE report, package detail pages
- **CSS variables** — light and dark themes matching the ActiveState design system
- **GitHub Actions** — builds and deploys to GitHub Pages on every push to `main`

---

## Repo structure

```
├── public/data/
│   ├── catalog.json      package list + versions (refreshed manually)
│   └── audit.json        CVE scan results (refreshed manually)
├── src/                  React app
├── scripts/              data pipeline (Python + Docker)
└── .github/workflows/    CI deploy to GitHub Pages
```

---

## Refreshing the data

```bash
cp .env.example .env          # add your CATALOG_TOKEN
cd scripts
python3 fetch_data.py         # fetches all packages → ../public/data/catalog.json
bash run_scan.sh --all        # runs CVE scan     → ../public/data/audit.json
cd ..
git add public/data/
git commit -m "chore: refresh catalog + CVE data"
git push                      # triggers deploy
```

Fetch takes ~5 min (1700+ packages, 30 concurrent requests). Scan takes ~5 min (OSV lookup, no installs).

---

## Local development

```bash
npm install
npm run dev       # http://localhost:5173
```

---

## Scripts (`scripts/`)

| File | Purpose |
|---|---|
| `fetch_data.py` | Fetch all packages + versions from the private index |
| `prepare_scan.py` | Build `scan_requirements.txt` (`--all` for full catalog) |
| `run_scan.sh` | Build Docker image → run pip-audit → write `audit.json` |
| `Dockerfile` | `python:3.12-slim` + `pip-audit` |
| `generate_report.py` | Parse `audit.json` → standalone HTML (pre-React fallback) |

---

## Packages with no files

11 packages appear in the index but have no files: `boolean-py`, `datetime`, `deepmerge`, `durationpy`, `fasteners`, `funcy`, `humanfriendly`, `pycparser`, `readme-renderer`, `setuptools-scm[toml]`, `websockets`. These show `—` in the versions column. Known catalog issue.
