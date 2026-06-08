# CuratedCatalog UI

A demo interface for the ActiveState Curated Catalog — a private PyPI index of curated, vetted Python packages. Built for customer POVs and sales demos.

Live: **https://activestate.github.io/CuratedCatalogUI/**

---

## What this is

The ActiveState Curated Catalog is a private PyPI-compatible package index. This UI gives customers a visual overview of the catalog's contents and security posture — two things that are otherwise invisible when using the index via `pip`.

### Catalog browser (`/`)

Full package table with inline information — no need to click into individual packages:

- **Package name** — single-line monospace, never clipped
- **Versions** — all version pills in the row, latest highlighted; column auto-sizes to content
- **Vulnerabilities Summary** — CVE alias or vuln ID pill per vulnerability (`CVE-2026-48710`, `PYSEC-...`), or a green **Clean** badge if none. Sortable — click to put vulnerable packages first.
- **View ↗** — direct link to the package's page in the private index

Live search + sortable columns (name, CVE status).

### CVE scan report (`/cve-report`)

Opens on the **Vulnerable** filter by default. The catalog is scanned against the [OSV advisory database](https://osv.dev/) using `pip-audit` inside a Docker container.

- **Stat cards** — packages scanned / vulnerable / total CVEs / clean
- **Filter** — All / Vulnerable / Clean
- **Per-row** — version pill, vuln ID, CVE aliases, fix version, truncated description
- **Description modal** — click `ⓘ` to open a centered popup with full details. If a package has multiple CVEs, click any vuln pill in the modal to switch to that vulnerability's description.

The scanner uses `--disable-pip --no-deps` — checks exact pinned versions against OSV without installing anything (~5 min for 1700+ packages).

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
│   ├── catalog.json      package list + versions + index URL (refreshed manually)
│   └── audit.json        CVE scan results (refreshed manually)
├── src/
│   ├── components/       Navbar, VersionPill, CvePill, StatCard, DescriptionCell
│   ├── context/          DataContext — loads + normalizes both JSON files
│   ├── pages/            CatalogPage, ScanReportPage, PackageDetailPage
│   └── styles/           CSS variables (tokens.css) + global base styles
├── scripts/              data pipeline (Python + Docker)
└── .github/workflows/    CI deploy to GitHub Pages
```

---

## Switching to a different customer index

Each customer has their own private index with a unique UUID. To point the UI at a different index:

1. Edit `.env` — update the three values:
   ```
   CATALOG_USER=your_user_here
   CATALOG_TOKEN=<customer token>
   CATALOG_INDEX_ID=<customer index UUID>
   ```

2. Re-fetch data and re-scan:
   ```bash
   cd scripts
   python3 fetch_data.py    # pulls packages from the new index
   bash run_scan.sh --all   # re-runs CVE scan against the new package set
   cd ..
   ```

3. Push:
   ```bash
   git add public/data/
   git commit -m "chore: switch to <customer name> index"
   git push                 # GitHub Actions redeploys automatically
   ```

The index UUID is stored **only** in `.env` (gitignored) and baked into `public/data/catalog.json` at fetch time — no code changes, no rebuild needed.

---

## Refreshing the data (same customer)

```bash
cd scripts
python3 fetch_data.py         # → ../public/data/catalog.json
bash run_scan.sh --all        # → ../public/data/audit.json
cd ..
git add public/data/
git commit -m "chore: refresh catalog + CVE data"
git push
```

Fetch ~5 min (1700+ packages, 30 concurrent requests). Scan ~5 min (OSV lookup, no package installs).

---

## Local development

```bash
npm install
npm run dev       # http://localhost:5173/CuratedCatalogUI/
```

---

## Scripts (`scripts/`)

| File | Purpose |
|---|---|
| `fetch_data.py` | Fetch all packages + versions → `public/data/catalog.json` |
| `prepare_scan.py` | Build `scan_requirements.txt` (`--all` for full catalog) |
| `run_scan.sh` | Build Docker image → run pip-audit → `public/data/audit.json` |
| `Dockerfile` | `python:3.12-slim` + `pip-audit` |
| `generate_report.py` | Parse `audit.json` → standalone HTML (pre-React fallback) |

---

## Known catalog issues

- **11 packages with no files** — listed in the main index but have no artifacts: `boolean-py`, `datetime`, `deepmerge`, `durationpy`, `fasteners`, `funcy`, `humanfriendly`, `pycparser`, `readme-renderer`, `setuptools-scm[toml]`, `websockets`. Show `—` in the versions column.
- **5 packages skipped by pip-audit** — `intel-numpy`, `intel-scipy`, `pillow-with-lcms`, `scantree`, `swat` (not found on PyPI). Excluded from scan results — neither Clean nor Vulnerable.
