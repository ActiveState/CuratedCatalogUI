# CuratedCatalog UI

A demo interface for the ActiveState Curated Catalog — a curated, vetted package index covering multiple languages. Built for customer POVs and sales demos.

Live: **https://activestate.github.io/CuratedCatalogUI/**

---

## What this is

The ActiveState Curated Catalog provides private, security-vetted package indexes. This UI gives customers a visual overview of catalog contents and security posture across languages — things that are otherwise invisible when consuming the index via a package manager.

The UI is multi-customer. Each customer gets their own package + CVE data at `public/data/<customer>/<lang>/`. The active customer is shown as a pill in the navbar; to enable a full customer switcher, set `CUSTOMER_SWITCHER_ACTIVE = true` in `src/components/Navbar.tsx`.

**Currently live:** LDPoV — Python (1730 packages), JavaScript (753 packages), Java/Maven (5357 packages).

### Catalog browser (`/#/:lang`)

Full package table with inline information:

- **Package name** — monospace, truncates gracefully on long names
- **Versions** — all version pills, latest highlighted; consistent column width across languages
- **Vulnerabilities Summary** — CVE alias or vuln ID pill per vulnerability, or a green **Clean** badge. Sortable.
- **View ↗** *(Python only)* — link to the package's page in the private PyPI index

Live search + sortable columns (name, CVE status).

### CVE scan report (`/#/:lang/cve-report`)

Opens on the **Vulnerable** filter by default.

- **Stat cards** — packages scanned / vulnerable / total CVEs / clean / scanner tool; **Severity breakdown** card (Critical / High / Moderate / Low counts) when CVEs are present
- **Filter** — All / Vulnerable / Clean
- **Sortable columns** — Package (A–Z / Z–A) and Severity (worst-first / best-first); severity sort also orders vulns within each package worst-first
- **Per-row** — version pill, severity pill (Critical/High/Moderate/Low), vuln ID, CVE aliases, fix version, truncated description
- **Description modal** — click `ⓘ` for the full description with formatted text, headers, bold, code, links. Modal header shows severity pill + CVE aliases. Multi-CVE packages let you switch vulnerabilities inside the modal.
- **Unaudited notice** *(ASPoV internal only)* — packages with no published registry versions are excluded from scan; a banner shows the count with a toggle to browse the list. Hidden for customer-facing views.

**Python** — scanned with `pip-audit` + OSV inside Docker (`--disable-pip --no-deps`).  
**JavaScript** — scanned with `osv-scanner` via Docker against a generated `package-lock.json`.  
**Java** — scanned with `osv-scanner` `scan source --no-resolve` via Docker against a generated `pom.xml`.

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
│   ├── ldpov/                    ← active customer
│   │   ├── python/
│   │   │   ├── catalog.json      package list + versions
│   │   │   └── audit.json        pip-audit CVE results (normalized)
│   │   ├── javascript/
│   │   │   ├── catalog.json      npm package list + versions
│   │   │   └── audit.json        osv-scanner CVE results (normalized)
│   │   └── java/
│   │       ├── catalog.json      Maven artifact list + versions
│   │       └── audit.json        osv-scanner CVE results (normalized)
│   └── aspov/                    ← disabled (legacy ASPoV data)
│       ├── python/
│       └── javascript/
├── src/
│   ├── customers.ts              customer registry (id, label, languages[], disabled?)
│   ├── languages.ts              language registry (id, label, icon, scanTool, disabled?)
│   ├── context/
│   │   └── CustomerContext.tsx   selected-customer React context (defaults to ldpov)
│   ├── hooks/
│   │   └── useLanguageData.ts    per-customer/lang data fetch + cache
│   ├── components/               Navbar, VersionPill, CvePill, StatCard, DescriptionCell
│   ├── pages/                    CatalogPage, ScanReportPage, PackageDetailPage
│   └── styles/                   CSS variables (tokens.css) + global base styles
├── scripts/                      data pipelines (see below)
└── .github/workflows/            CI deploy to GitHub Pages
```

---

## Environment setup

Copy `.env.example` to `.env` and fill in your values:

```
# LDPoV credentials
LDPOV_USER=<user>
LDPOV_CATALOG_TOKEN=<token>
LDPOV_ORG_ID=<org UUID>

# LDPoV registry URLs
PYPI_URL=<private PyPI index URL>
NPM_URL=<private npm registry URL>
MAVEN_URL=<private Maven repo URL>
```

`.env` is gitignored — never commit real credentials.

---

## Refreshing data

Requires: `.env` loaded in your shell, AWS CLI logged in (`aws sso login`), Docker running.

> **Note:** Docker on this machine requires `--network host`. The scan scripts set this automatically.

### LDPoV Python

```bash
cd scripts
python3 fetch_ldpov_pypi.py      # → ../public/data/ldpov/python/catalog.json
bash run_ldpov_pypi_scan.sh      # → ../public/data/ldpov/python/audit.json
```

### LDPoV JavaScript

```bash
cd scripts
python3 fetch_ldpov_npm.py       # → ../public/data/ldpov/javascript/catalog.json
bash run_ldpov_npm_scan.sh       # → ../public/data/ldpov/javascript/audit.json
```

### LDPoV Java (Maven)

```bash
cd scripts
python3 fetch_ldpov_maven.py     # → ../public/data/ldpov/java/catalog.json
bash run_ldpov_maven_scan.sh     # → ../public/data/ldpov/java/audit.json
```

### Commit + push

```bash
cd ..
git add public/data/ldpov/
git commit -m "chore: refresh LDPoV catalog + CVE data"
git push
```

---

## Local development

```bash
npm install
npm run dev       # http://localhost:5173/CuratedCatalogUI/
```

Navigate to `/#/python`, `/#/javascript`, or `/#/java`. The root redirects to `/#/python`.

---

## Scripts (`scripts/`)

| File | Language | Purpose |
|---|---|---|
| `fetch_ldpov_pypi.py` | Python | Crawl private PyPI index → `ldpov/python/catalog.json` |
| `run_ldpov_pypi_scan.sh` | Python | pip-audit in Docker → `ldpov/python/audit.json` |
| `fetch_ldpov_npm.py` | JavaScript | S3 redirect_map + npm registry → `ldpov/javascript/catalog.json` |
| `run_ldpov_npm_scan.sh` | JavaScript | osv-scanner in Docker → `ldpov/javascript/audit.json` |
| `normalize_npm_audit.py` | JavaScript | Normalize osv-scanner JSON → shared audit.json schema; extracts severity from `database_specific.severity` |
| `fetch_ldpov_maven.py` | Java | S3 `repo-type=maven2` redirect_map (`group:artifact:version` keys) → `ldpov/java/catalog.json` |
| `run_ldpov_maven_scan.sh` | Java | Build `pom.xml` → osv-scanner `scan source --no-resolve` in Docker → raw JSON |
| `normalize_maven_audit.py` | Java | Normalize osv-scanner v2 JSON → shared audit.json schema; includes all catalog packages; extracts severity |
| `Dockerfile` | Python | `python:3.12-slim` + `pip-audit` for Python scanning |

---

## Adding a new customer

1. Add an entry to `src/customers.ts` with `id`, `label`, `languages[]`, and `disabled: true` initially.
2. Add credentials to `.env`.
3. Write `scripts/fetch_<customer>_pypi.py`, `npm`, `maven` as needed (copy from ldpov equivalents).
4. Run fetches and scans → `public/data/<customer>/`.
5. Remove `disabled: true` from the customer entry to make it visible.
6. Set `CUSTOMER_SWITCHER_ACTIVE = true` in `src/components/Navbar.tsx` to enable the dropdown.

---

## Customer switcher

The customer pill in the navbar is currently non-interactive. To enable the full dropdown:

```ts
// src/components/Navbar.tsx
const CUSTOMER_SWITCHER_ACTIVE = true   // ← change this
```

All dropdown logic (state, refs, click-outside detection, language fallback) is already wired up and gated by this constant.
