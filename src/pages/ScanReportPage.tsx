import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useLanguageData } from '../hooks/useLanguageData'
import { useCustomer } from '../context/CustomerContext'
import { getLanguage } from '../languages'
import { CvePill } from '../components/CvePill'
import { SeverityPill } from '../components/SeverityPill'
import { StatCard } from '../components/StatCard'
import { DescriptionCell } from '../components/DescriptionCell'
import { VersionPill } from '../components/VersionPill'
import type { ScannedPackage, Vuln } from '../types'
import styles from './ScanReportPage.module.css'

type Filter  = 'all' | 'vuln' | 'clean'
type SortCol = 'pkg' | 'severity'

const SEV_ORDER: Record<string, number> = { CRITICAL: 4, HIGH: 3, MODERATE: 2, LOW: 1 }

type CleanRow = { type: 'clean'; pkg: ScannedPackage; n: number }
type VulnRow  = { type: 'vuln';  pkg: ScannedPackage; vuln: Vuln; vi: number; n: number; pkgVulns: Vuln[] }
type RowData  = CleanRow | VulnRow

export function ScanReportPage() {
  const { lang = 'python' } = useParams<{ lang: string }>()
  const { customerId } = useCustomer()
  const { packages, scanned, loading, error } = useLanguageData(lang)
  const language = getLanguage(lang)

  const [query, setQuery]           = useState('')
  const [filter, setFilter]         = useState<Filter>('vuln')
  const [showUnaudited, setShowUnaudited] = useState(false)
  const [sortCol, setSortCol]       = useState<SortCol>('pkg')
  const [sortDir, setSortDir]       = useState<1 | -1>(1)

  function handleSort(col: SortCol) {
    if (sortCol === col) setSortDir(d => (d === 1 ? -1 : 1))
    else { setSortCol(col); setSortDir(col === 'severity' ? -1 : 1) }
  }

  function arrow(col: SortCol) {
    if (sortCol === col) return <span className={styles.sortActive}>{sortDir === 1 ? '↑' : '↓'}</span>
    return <span className={styles.sortIdle}>⇅</span>
  }

  const stats = useMemo(() => {
    const bySeverity: Record<string, number> = { CRITICAL: 0, HIGH: 0, MODERATE: 0, LOW: 0 }
    scanned.forEach(p => p.vulns.forEach(v => {
      const s = v.severity?.toUpperCase()
      if (s && s in bySeverity) bySeverity[s]++
    }))
    return {
      total: scanned.length,
      vuln:  scanned.filter(p => p.vulns.length > 0).length,
      cves:  scanned.reduce((n, p) => n + p.vulns.length, 0),
      clean: scanned.filter(p => p.vulns.length === 0).length,
      bySeverity,
    }
  }, [scanned])

  const flatRows = useMemo((): RowData[] => {
    const q = query.toLowerCase()
    let res = q ? scanned.filter(p => p.name.toLowerCase().includes(q)) : scanned
    if (filter === 'vuln')  res = res.filter(p => p.vulns.length > 0)
    if (filter === 'clean') res = res.filter(p => p.vulns.length === 0)

    const maxSev = (p: ScannedPackage) =>
      p.vulns.reduce((m, v) => Math.max(m, SEV_ORDER[v.severity?.toUpperCase() ?? ''] ?? 0), 0)

    res = [...res].sort((a, b) => {
      if (sortCol === 'pkg') {
        const an = a.name.toLowerCase(), bn = b.name.toLowerCase()
        return an < bn ? -sortDir : an > bn ? sortDir : 0
      }
      const diff = maxSev(b) - maxSev(a)
      return diff !== 0 ? diff * sortDir : 0
    })

    const rows: RowData[] = []
    let n = 0
    res.forEach(pkg => {
      if (pkg.vulns.length === 0) {
        rows.push({ type: 'clean', pkg, n: ++n })
      } else {
        const pkgVulns = sortCol === 'severity'
          ? [...pkg.vulns].sort((a, b) =>
              ((SEV_ORDER[b.severity?.toUpperCase() ?? ''] ?? 0) -
               (SEV_ORDER[a.severity?.toUpperCase() ?? ''] ?? 0)) * sortDir)
          : pkg.vulns
        pkgVulns.forEach((vuln, vi) => {
          rows.push({ type: 'vuln', pkg, vuln, vi, n: ++n, pkgVulns })
        })
      }
    })
    return rows
  }, [scanned, query, filter, sortCol, sortDir])

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
        <StatCard label="Scanner" value={language.scanTool} />
        {stats.cves > 0 && (
          <div className={styles.sevBreakCard}>
            <div className={styles.sevBreakLabel}>Severity</div>
            <div className={styles.sevBreakGrid}>
              {(['CRITICAL', 'HIGH', 'MODERATE', 'LOW'] as const).map(s => (
                <div key={s} className={styles.sevBreakRow}>
                  <SeverityPill severity={s} />
                  <span className={styles.sevBreakCount}>{stats.bySeverity[s]}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      {customerId === 'aspov' && packages.length > scanned.length && (() => {
        const scannedNames = new Set(scanned.map(p => p.name))
        const unaudited = packages.filter(p => !scannedNames.has(p.name))
        return (
          <>
            <div className={`${styles.notice} ${showUnaudited ? styles.noticeOpen : ''}`}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{flexShrink:0}}>
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <span>
                <b>{unaudited.length.toLocaleString()}</b> of {packages.length.toLocaleString()} catalog
                packages were excluded from the scan — they have no published versions in the registry and cannot be audited.
              </span>
              <button className={styles.noticeBtn} onClick={() => setShowUnaudited(o => !o)}>
                {showUnaudited ? 'Hide unaudited packages' : 'View unaudited packages'}
              </button>
            </div>
            {showUnaudited && (
              <div className={styles.unauditedList}>
                {unaudited.map(p => (
                  <span key={p.name} className={styles.unauditedPkg}>{p.name}</span>
                ))}
              </div>
            )}
          </>
        )
      })()}

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
            <p>{scanned.length === 0 ? 'No scan data available yet for this language.' : 'Try a different search or filter.'}</p>
          </div>
        ) : (
          <div className={styles.tableScroll}><table>
            <colgroup>
              <col className={styles.colIdx} />
              <col className={styles.colPkg} />
              <col className={styles.colVer} />
              <col className={styles.colStatus} />
              <col className={styles.colVulnId} />
              <col className={styles.colCve} />
              <col className={styles.colFix} />
              <col className={styles.colDesc} />
            </colgroup>
            <thead>
              <tr>
                <th>#</th>
                <th className={`sortable${sortCol === 'pkg' ? ' sorted' : ''}`} onClick={() => handleSort('pkg')}>
                  Package {arrow('pkg')}
                </th>
                <th>Version</th>
                <th className={`sortable${sortCol === 'severity' ? ' sorted' : ''}`} onClick={() => handleSort('severity')}>
                  Severity {arrow('severity')}
                </th>
                <th>Vuln ID</th>
                <th>CVE Aliases</th>
                <th>Fix Version</th>
                <th>Description</th>
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
                  <td><SeverityPill severity={row.vuln.severity} /></td>
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
                      allVulns={row.pkgVulns}
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
