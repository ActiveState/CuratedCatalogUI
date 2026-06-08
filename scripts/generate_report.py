#!/usr/bin/env python3
"""Read results/audit.json produced by pip-audit and write scan_report.html."""

import json
import datetime
import os

AUDIT_JSON = os.path.join("results", "audit.json")

with open(AUDIT_JSON) as f:
    raw = json.load(f)

# pip-audit --format json outputs a list; older versions wrap in {"dependencies": [...]}
deps = raw if isinstance(raw, list) else raw.get("dependencies", [])

scanned = []
for dep in deps:
    name = dep.get("name", "")
    version = dep.get("version", "")
    vulns = dep.get("vulns", [])
    findings = []
    for v in vulns:
        aliases = v.get("aliases", [])
        cves = [a for a in aliases if a.startswith("CVE-")]
        findings.append({
            "id": v.get("id", ""),
            "cves": cves,
            "fix": v.get("fix_versions", []),
            "description": v.get("description", ""),
        })
    scanned.append({"name": name, "version": version, "vulns": findings})

total_pkgs = len(scanned)
vulnerable_pkgs = sum(1 for p in scanned if p["vulns"])
total_vulns = sum(len(p["vulns"]) for p in scanned)
generated = datetime.datetime.utcnow().strftime("%b %d, %Y %H:%M UTC")

data_json = json.dumps(scanned, separators=(",", ":"))
# Escape </script> and <!-- so CVE descriptions can't break the <script> block
data_json = data_json.replace("</", "<\\/")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CVE Scan Report — Curated Catalog</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f1117; color: #e2e8f0; min-height: 100vh; }}
    header {{ background: #1a1d27; border-bottom: 1px solid #2d3148; padding: 20px 32px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
    header h1 {{ font-size: 1.4rem; font-weight: 600; color: #a78bfa; letter-spacing: -0.02em; }}
    header .subtitle {{ font-size: 0.8rem; color: #64748b; margin-top: 2px; }}
    .nav-link {{ margin-left: auto; font-size: 0.82rem; color: #7c3aed; text-decoration: none; border: 1px solid #4c3799; padding: 5px 14px; border-radius: 6px; white-space: nowrap; }}
    .nav-link:hover {{ background: #2d1e6e; }}
    .summary {{ display: flex; gap: 16px; padding: 20px 32px; flex-wrap: wrap; }}
    .stat {{ background: #1a1d27; border: 1px solid #2d3148; border-radius: 10px; padding: 16px 24px; min-width: 160px; }}
    .stat .label {{ font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; margin-bottom: 6px; }}
    .stat .value {{ font-size: 2rem; font-weight: 700; line-height: 1; }}
    .stat.ok .value {{ color: #86efac; }}
    .stat.warn .value {{ color: #fbbf24; }}
    .stat.bad .value {{ color: #f87171; }}
    .stat.neutral .value {{ color: #94a3b8; }}
    .toolbar {{ padding: 16px 32px; display: flex; gap: 12px; align-items: center; background: #13161f; border-bottom: 1px solid #1e2133; flex-wrap: wrap; }}
    .search-wrap {{ position: relative; flex: 1; min-width: 200px; max-width: 400px; }}
    .search-wrap svg {{ position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #475569; pointer-events: none; }}
    #search {{ width: 100%; padding: 9px 12px 9px 38px; background: #1e2235; border: 1px solid #2d3556; border-radius: 8px; color: #e2e8f0; font-size: 0.88rem; outline: none; transition: border-color 0.15s; }}
    #search:focus {{ border-color: #7c3aed; }}
    #search::placeholder {{ color: #475569; }}
    .filter-btns {{ display: flex; gap: 8px; }}
    .filter-btn {{ padding: 6px 14px; border-radius: 6px; border: 1px solid #2d3556; background: #1e2235; color: #94a3b8; font-size: 0.78rem; cursor: pointer; transition: all 0.15s; }}
    .filter-btn:hover {{ border-color: #7c3aed; color: #e2e8f0; }}
    .filter-btn.active {{ background: #2d1e6e; border-color: #7c3aed; color: #c4b5fd; }}
    .count {{ font-size: 0.82rem; color: #64748b; white-space: nowrap; margin-left: auto; }}
    .count span {{ color: #94a3b8; font-weight: 600; }}
    .generated {{ font-size: 0.78rem; color: #3d4466; }}
    .table-wrap {{ padding: 0 32px 40px; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 0.875rem; }}
    thead th {{ text-align: left; padding: 10px 16px; background: #1a1d27; color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; border-bottom: 1px solid #2d3148; white-space: nowrap; }}
    tbody tr {{ border-bottom: 1px solid #1a1d2b; transition: background 0.1s; }}
    tbody tr:hover {{ background: #181b2a; }}
    tbody td {{ padding: 11px 16px; vertical-align: top; }}
    td.pkg {{ font-family: "SF Mono","Fira Code",monospace; font-size: 0.82rem; color: #c4b5fd; white-space: nowrap; }}
    td.ver {{ font-family: "SF Mono","Fira Code",monospace; font-size: 0.78rem; color: #7dd3fc; white-space: nowrap; }}
    td.vuln-id {{ font-family: "SF Mono","Fira Code",monospace; font-size: 0.75rem; color: #f97316; white-space: nowrap; }}
    td.cve {{ font-family: "SF Mono","Fira Code",monospace; font-size: 0.75rem; }}
    .cve-tag {{ display: inline-block; background: #2a1a0a; border: 1px solid #78350f; color: #fbbf24; font-size: 0.7rem; padding: 1px 7px; border-radius: 4px; margin: 1px 2px 1px 0; white-space: nowrap; }}
    td.fix {{ font-family: "SF Mono","Fira Code",monospace; font-size: 0.75rem; color: #86efac; white-space: nowrap; }}
    .no-fix {{ color: #475569; font-size: 0.75rem; font-style: italic; }}
    td.desc {{ font-size: 0.78rem; color: #94a3b8; max-width: 420px; line-height: 1.5; }}
    .status-ok {{ display: inline-block; background: #1a2e1a; border: 1px solid #2d5a2d; color: #86efac; font-size: 0.72rem; padding: 2px 10px; border-radius: 4px; }}
    .status-vuln {{ display: inline-block; background: #2a1010; border: 1px solid #5a2020; color: #f87171; font-size: 0.72rem; padding: 2px 10px; border-radius: 4px; }}
    #empty-state {{ text-align: center; padding: 80px 32px; color: #3d4466; display: none; }}
    #empty-state h2 {{ font-size: 1.1rem; margin-bottom: 8px; color: #475569; }}
    @media (max-width: 640px) {{ header, .summary, .toolbar, .table-wrap {{ padding-left: 16px; padding-right: 16px; }} }}
  </style>
</head>
<body>
<header>
  <div>
    <h1>CVE Scan Report</h1>
    <div class="subtitle">Curated Catalog — pip-audit via OSV</div>
  </div>
  <a class="nav-link" href="index.html">&#8592; Package Catalog</a>
</header>

<div class="summary">
  <div class="stat neutral">
    <div class="label">Packages Scanned</div>
    <div class="value">{total_pkgs}</div>
  </div>
  <div class="stat {'bad' if vulnerable_pkgs > 0 else 'ok'}">
    <div class="label">Vulnerable</div>
    <div class="value">{vulnerable_pkgs}</div>
  </div>
  <div class="stat {'warn' if total_vulns > 0 else 'ok'}">
    <div class="label">Total CVEs</div>
    <div class="value">{total_vulns}</div>
  </div>
  <div class="stat ok">
    <div class="label">Clean</div>
    <div class="value">{total_pkgs - vulnerable_pkgs}</div>
  </div>
  <div class="stat neutral" style="margin-left:auto; min-width:auto">
    <div class="label">Generated</div>
    <div class="value" style="font-size:0.95rem; color:#64748b; padding-top:4px">{generated}</div>
  </div>
</div>

<div class="toolbar">
  <div class="search-wrap">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
    </svg>
    <input id="search" type="text" placeholder="Search packages&#x2026;" autocomplete="off">
  </div>
  <div class="filter-btns">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="vuln">Vulnerable only</button>
    <button class="filter-btn" data-filter="clean">Clean only</button>
  </div>
  <div class="count">Showing <span id="shown-count">—</span> findings</div>
</div>

<div class="table-wrap">
  <table id="report-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Package</th>
        <th>Version</th>
        <th>Status</th>
        <th>Vuln ID</th>
        <th>CVE Aliases</th>
        <th>Fix Version</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="empty-state">
    <h2>No results match your filter</h2>
    <p>Try changing the search or filter.</p>
  </div>
</div>

<script>
const ALL_PKGS = {data_json};

let activeFilter = "all";

function escHtml(s) {{
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}}

function buildRows(pkgs) {{
  const rows = [];
  let rowIndex = 0;
  pkgs.forEach(pkg => {{
    if (pkg.vulns.length === 0) {{
      rowIndex++;
      rows.push(
        '<tr data-status="clean">' +
        '<td style="color:#3d4466;font-size:.78rem">' + rowIndex + '</td>' +
        '<td class="pkg">' + escHtml(pkg.name) + '</td>' +
        '<td class="ver">' + escHtml(pkg.version) + '</td>' +
        '<td><span class="status-ok">Clean</span></td>' +
        '<td>—</td><td>—</td><td>—</td><td class="desc" style="color:#3d4466">No known vulnerabilities</td>' +
        '</tr>'
      );
    }} else {{
      pkg.vulns.forEach((v, vi) => {{
        rowIndex++;
        const cveTags = v.cves.length
          ? v.cves.map(c => '<span class="cve-tag">' + escHtml(c) + '</span>').join("")
          : '<span style="color:#475569;font-size:.75rem">—</span>';
        const fixStr = v.fix.length
          ? v.fix.map(f => escHtml(f)).join(", ")
          : '<span class="no-fix">No fix available</span>';
        const desc = v.description.length > 280
          ? escHtml(v.description.slice(0, 280)) + '…'
          : escHtml(v.description);
        rows.push(
          '<tr data-status="vuln">' +
          '<td style="color:#3d4466;font-size:.78rem">' + rowIndex + '</td>' +
          '<td class="pkg">' + (vi === 0 ? escHtml(pkg.name) : '') + '</td>' +
          '<td class="ver">' + (vi === 0 ? escHtml(pkg.version) : '') + '</td>' +
          '<td>' + (vi === 0 ? '<span class="status-vuln">Vulnerable</span>' : '') + '</td>' +
          '<td class="vuln-id">' + escHtml(v.id) + '</td>' +
          '<td class="cve">' + cveTags + '</td>' +
          '<td class="fix">' + fixStr + '</td>' +
          '<td class="desc">' + desc + '</td>' +
          '</tr>'
        );
      }});
    }}
  }});
  return rows;
}}

function render() {{
  const query = document.getElementById("search").value.trim().toLowerCase();
  let pkgs = ALL_PKGS;
  if (query) pkgs = pkgs.filter(p => p.name.toLowerCase().includes(query));
  if (activeFilter === "vuln") pkgs = pkgs.filter(p => p.vulns.length > 0);
  if (activeFilter === "clean") pkgs = pkgs.filter(p => p.vulns.length === 0);

  const rows = buildRows(pkgs);
  const tbody = document.getElementById("tbody");
  const emptyEl = document.getElementById("empty-state");
  const tableEl = document.getElementById("report-table");

  if (rows.length === 0) {{
    tableEl.style.display = "none";
    emptyEl.style.display = "block";
    document.getElementById("shown-count").textContent = "0";
  }} else {{
    tableEl.style.display = "table";
    emptyEl.style.display = "none";
    tbody.innerHTML = rows.join("");
    document.getElementById("shown-count").textContent = rows.length.toLocaleString();
  }}
}}

document.querySelectorAll(".filter-btn").forEach(btn => {{
  btn.addEventListener("click", () => {{
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeFilter = btn.dataset.filter;
    render();
  }});
}});

let searchTimer;
document.getElementById("search").addEventListener("input", () => {{
  clearTimeout(searchTimer);
  searchTimer = setTimeout(render, 150);
}});

render();
</script>
</body>
</html>"""

with open("scan_report.html", "w") as f:
    f.write(html)

vuln_summary = [(p["name"], p["version"], len(p["vulns"])) for p in scanned if p["vulns"]]
print(f"scan_report.html written — {total_pkgs} packages, {vulnerable_pkgs} vulnerable, {total_vulns} CVEs")
if vuln_summary:
    print("Vulnerable packages:")
    for name, ver, count in vuln_summary:
        print(f"  {name}=={ver}  ({count} vuln{'s' if count > 1 else ''})")
else:
    print("All packages clean.")
