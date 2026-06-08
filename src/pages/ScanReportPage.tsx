import { useMemo, useState } from 'react'
import { useData } from '../context/DataContext'
import { CvePill } from '../components/CvePill'
import { StatCard } from '../components/StatCard'
import { DescriptionCell } from '../components/DescriptionCell'
import { VersionPill } from '../components/VersionPill'
import type { ScannedPackage, Vuln } from '../types'
import styles from './ScanReportPage.module.css'

type Filter = 'all' | 'vuln' | 'clean'

type CleanRow = { type: 'clean'; pkg: ScannedPackage; n: number }
type VulnRow  = { type: 'vuln';  pkg: ScannedPackage; vuln: Vuln; vi: number; n: number }
type RowData  = CleanRow | VulnRow

export function ScanReportPage() {
  const { scanned, loading, error } = useData()
  const [query, setQuery]   = useState('')
  const [filter, setFilter] = useState<Filter>('all')

  const stats = useMemo(() => ({
    total: scanned.length,
    vuln:  scanned.filter(p => p.vulns.length > 0).length,
    cves:  scanned.reduce((n, p) => n + p.vulns.length, 0),
    clean: scanned.filter(p => p.vulns.length === 0).length,
  }), [scanned])

  const flatRows = useMemo((): RowData[] => {
    const q = query.toLowerCase()
    let res = q ? scanned.filter(p => p.name.toLowerCase().includes(q)) : scanned
    if (filter === 'vuln')  res = res.filter(p => p.vulns.length > 0)
    if (filter === 'clean') res = res.filter(p => p.vulns.length === 0)

    const rows: RowData[] = []
    let n = 0
    res.forEach(pkg => {
      if (pkg.vulns.length === 0) {
        rows.push({ type: 'clean', pkg, n: ++n })
      } else {
        pkg.vulns.forEach((vuln, vi) => {
          rows.push({ type: 'vuln', pkg, vuln, vi, n: ++n })
        })
      }
    })
    return rows
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
        <p className="count-label">Showing <b>{flatRows.length.toLocaleString()}</b> rows</p>
      </div>

      <div className="card">
        {flatRows.length === 0 ? (
          <div className="empty-state">
            <h3>No results match your filter</h3>
            <p>Try a different search or filter.</p>
          </div>
        ) : (
          <div className={styles.tableScroll}><table>
            <thead>
              <tr>
                <th style={{ width: 52 }}>#</th>
                <th style={{ width: '24%' }}>Package</th>
                <th style={{ width: '11%' }}>Version</th>
                <th style={{ width: '10%' }}>Status</th>
                <th style={{ width: '12%' }}>Vuln ID</th>
                <th style={{ width: '11%' }}>CVE Aliases</th>
                <th style={{ width: '12%' }}>Fix Version</th>
                <th style={{ width: '17%' }}>Description</th>
              </tr>
            </thead>
            <tbody>
              {flatRows.map(row => row.type === 'clean' ? (
                <tr key={row.pkg.name}>
                  <td className={styles.idx}>{row.n}</td>
                  <td className={styles.pkgName}>{row.pkg.name}</td>
                  <td><VersionPill version={row.pkg.version} latest /></td>
                  <td><span className={styles.statusOk}>Clean</span></td>
                  <td>—</td><td>—</td><td>—</td>
                  <td className={`${styles.desc} ${styles.muted}`}>No known vulnerabilities</td>
                </tr>
              ) : (
                <tr key={`${row.pkg.name}-${row.vuln.id}-${row.vi}`}>
                  <td className={styles.idx}>{row.n}</td>
                  <td className={styles.pkgName}>{row.vi === 0 ? row.pkg.name : ''}</td>
                  <td>{row.vi === 0 ? <VersionPill version={row.pkg.version} latest /> : ''}</td>
                  <td>{row.vi === 0 ? <span className={styles.statusVuln}>Vulnerable</span> : ''}</td>
                  <td className={styles.vulnId}>{row.vuln.id}</td>
                  <td className={styles.cveCol}>
                    {row.vuln.cves.length > 0
                      ? row.vuln.cves.map(c => <CvePill key={c} id={c} />)
                      : <span className={styles.muted}>—</span>}
                  </td>
                  <td className={styles.fix}>
                    {row.vuln.fix.length > 0
                      ? row.vuln.fix.join(', ')
                      : <span className={styles.muted}>No fix available</span>}
                  </td>
                  <td className={styles.desc}>
                    <DescriptionCell
                      text={row.vuln.description}
                      packageName={row.pkg.name}
                      version={row.pkg.version}
                      allVulns={row.pkg.vulns}
                      vulnIndex={row.vi}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table></div>
        )}
      </div>
    </div>
  )
}
