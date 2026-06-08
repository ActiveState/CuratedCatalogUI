import { useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useData } from '../context/DataContext'
import { VersionPill } from '../components/VersionPill'
import { CvePill } from '../components/CvePill'
import styles from './PackageDetailPage.module.css'

export function PackageDetailPage() {
  const { name } = useParams<{ name: string }>()
  const { packages, scanned, indexUrl, loading } = useData()

  const pkg = useMemo(
    () => packages.find(p => p.name === name),
    [packages, name]
  )
  const scan = useMemo(
    () => scanned.find(p => p.name === name),
    [scanned, name]
  )

  if (loading) return <div className={styles.loading}><div className={styles.spinner} /></div>

  if (!pkg) return (
    <div className="page-wrap">
      <div className="empty-state" style={{ marginTop: 40 }}>
        <h3>Package not found</h3>
        <p>"{name}" is not in the catalog.</p>
        <Link to="/" className={styles.back}>← Back to catalog</Link>
      </div>
    </div>
  )

  const vulnCount = scan?.vulns.length ?? 0

  return (
    <div className="page-wrap">
      <div className={styles.header}>
        <Link to="/" className={styles.back}>← Packages</Link>
        <div className={styles.titleRow}>
          <h1 className={styles.pkgName}>{pkg.name}</h1>
          {vulnCount > 0
            ? <span className={styles.badgeVuln}>{vulnCount} CVE{vulnCount > 1 ? 's' : ''}</span>
            : <span className={styles.badgeOk}>Clean</span>
          }
          <a className={styles.indexLink} href={`${indexUrl}${pkg.name}/`} target="_blank" rel="noopener">
            View in index ↗
          </a>
        </div>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Versions <span className={styles.count}>({pkg.versions.length})</span></h2>
        <div className="card" style={{ padding: '16px 20px' }}>
          {pkg.versions.length === 0
            ? <p className={styles.muted}>No files available in the index.</p>
            : [...pkg.versions].reverse().map((v, i) => (
                <VersionPill key={v} version={v} latest={i === 0} />
              ))
          }
        </div>
      </div>

      {scan && scan.vulns.length > 0 && (
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>
            CVE Findings
            <span className={styles.scannedVer}>scanned version: <code>{scan.version}</code></span>
          </h2>
          <div className="card">
            <table>
              <thead>
                <tr>
                  <th>Vuln ID</th>
                  <th>CVE Aliases</th>
                  <th>Fix Version</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {scan.vulns.map(v => (
                  <tr key={v.id}>
                    <td className={styles.vulnId}>{v.id}</td>
                    <td>
                      {v.cves.length > 0
                        ? v.cves.map(c => <CvePill key={c} id={c} />)
                        : <span className={styles.muted}>—</span>}
                    </td>
                    <td className={styles.fix}>
                      {v.fix.length > 0 ? v.fix.join(', ') : <span className={styles.muted}>No fix available</span>}
                    </td>
                    <td className={styles.desc}>{v.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {(!scan || scan.vulns.length === 0) && pkg.versions.length > 0 && (
        <div className={styles.section}>
          <div className={styles.cleanMsg}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            No known vulnerabilities for the scanned version.
          </div>
        </div>
      )}
    </div>
  )
}
