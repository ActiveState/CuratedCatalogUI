import { useMemo, useState } from 'react'
import { useData } from '../context/DataContext'
import { CvePill } from '../components/CvePill'
import { StatCard } from '../components/StatCard'
import { DescriptionCell } from '../components/DescriptionCell'
import styles from './ScanReportPage.module.css'

type Filter = 'all' | 'vuln' | 'clean'

export function ScanReportPage() {
  const { scanned, loading, error } = useData()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<Filter>('all')

  const stats = useMemo(() => ({
    total:   scanned.length,
    vuln:    scanned.filter(p => p.vulns.length > 0).length,
    cves:    scanned.reduce((n, p) => n + p.vulns.length, 0),
    clean:   scanned.filter(p => p.vulns.length === 0).length,
  }), [scanned])

  const rows = useMemo(() => {
    const q = query.toLowerCase()
    let res = q ? scanned.filter(p => p.name.toLowerCase().includes(q)) : scanned
    if (filter === 'vuln')  res = res.filter(p => p.vulns.length > 0)
    if (filter === 'clean') res = res.filter(p => p.vulns.length === 0)

    const out: React.ReactNode[] = []
    let n = 0
    res.forEach(pkg => {
      if (pkg.vulns.length === 0) {
        n++
        out.push(
          <tr key={pkg.name} data-status="clean">
            <td className={styles.idx}>{n}</td>
            <td className={styles.pkgName}>{pkg.name}</td>
            <td className={styles.ver}>{pkg.version}</td>
            <td><span className={styles.statusOk}>Clean</span></td>
            <td>—</td><td>—</td><td>—</td>
            <td className={`${styles.desc} ${styles.muted}`}>No known vulnerabilities</td>
          </tr>
        )
      } else {
        pkg.vulns.forEach((v, vi) => {
          n++
          out.push(
            <tr key={`${pkg.name}-${v.id}`} data-status="vuln">
              <td className={styles.idx}>{n}</td>
              <td className={styles.pkgName}>{vi === 0 ? pkg.name : ''}</td>
              <td className={styles.ver}>{vi === 0 ? pkg.version : ''}</td>
              <td>{vi === 0 ? <span className={styles.statusVuln}>Vulnerable</span> : ''}</td>
              <td className={styles.vulnId}>{v.id}</td>
              <td className={styles.cveCol}>
                {v.cves.length > 0
                  ? v.cves.map(c => <CvePill key={c} id={c} />)
                  : <span className={styles.muted}>—</span>}
              </td>
              <td className={styles.fix}>
                {v.fix.length > 0
                  ? v.fix.join(', ')
                  : <span className={styles.muted}>No fix available</span>}
              </td>
              <td className={styles.desc}><DescriptionCell text={v.description} /></td>
            </tr>
          )
        })
      }
    })
    return { rows: out, count: n }
  }, [scanned, query, filter])

  if (loading) return (
    <div className={styles.loading}><div className={styles.spinner} /><span>Loading scan data…</span></div>
  )
  if (error) return <div className={styles.error}>Failed to load scan data: {error}</div>

  return (
    <div className="page-wrap">
      <div className={styles.stats}>
        <StatCard label="Packages Scanned" value={stats.total} variant="blue" />
        <StatCard label="Vulnerable"        value={stats.vuln}  variant={stats.vuln  > 0 ? 'red'   : 'green'} />
        <StatCard label="Total CVEs"        value={stats.cves}  variant={stats.cves  > 0 ? 'amber' : 'green'} />
        <StatCard label="Clean"             value={stats.clean} variant="green" />
        <StatCard label="Scanner" value="pip-audit · OSV" />
      </div>

      <div className="toolbar">
        <div className={styles.searchWrap}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            className={styles.search}
            type="text"
            placeholder="Search packages…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className={styles.filterBtns}>
          {(['all', 'vuln', 'clean'] as Filter[]).map(f => (
            <button
              key={f}
              className={`${styles.fbtn} ${filter === f ? styles.factive : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f === 'vuln' ? 'Vulnerable' : 'Clean'}
            </button>
          ))}
        </div>
        <p className="count-label">Showing <b>{rows.count.toLocaleString()}</b> rows</p>
      </div>

      <div className="card">
        {rows.rows.length === 0 ? (
          <div className="empty-state">
            <h3>No results match your filter</h3>
            <p>Try a different search or filter.</p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{ width: 40 }}>#</th>
                <th>Package</th>
                <th style={{ width: 110 }}>Version</th>
                <th style={{ width: 100 }}>Status</th>
                <th style={{ width: 160 }}>Vuln ID</th>
                <th style={{ width: 160 }}>CVE Aliases</th>
                <th style={{ width: 120 }}>Fix Version</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>{rows.rows}</tbody>
          </table>
        )}
      </div>
    </div>
  )
}
