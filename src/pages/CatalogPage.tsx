import { useMemo, useState } from 'react'
import { useData } from '../context/DataContext'
import { VersionPill } from '../components/VersionPill'
import styles from './CatalogPage.module.css'

type SortCol = 'name' | 'cve'

export function CatalogPage() {
  const { packages, scanned, generated, indexUrl, loading, error } = useData()
  const [query, setQuery]     = useState('')
  const [sortCol, setSortCol] = useState<SortCol>('name')
  const [sortDir, setSortDir] = useState<1 | -1>(1)

  const scanMap = useMemo(() => {
    const m = new Map(scanned.map(p => [p.name, p]))
    return m
  }, [scanned])

  const filtered = useMemo(() => {
    const q = query.toLowerCase()
    let res = q ? packages.filter(p => p.name.toLowerCase().includes(q)) : packages
    return [...res].sort((a, b) => {
      if (sortCol === 'cve') {
        const av = scanMap.get(a.name)?.vulns.length ?? -1
        const bv = scanMap.get(b.name)?.vulns.length ?? -1
        if (av !== bv) return bv > av ? sortDir : -sortDir
      }
      const an = a.name.toLowerCase(), bn = b.name.toLowerCase()
      return an < bn ? -sortDir : an > bn ? sortDir : 0
    })
  }, [packages, query, sortCol, sortDir, scanMap])

  function handleSort(col: SortCol) {
    if (sortCol === col) setSortDir(d => (d === 1 ? -1 : 1))
    else { setSortCol(col); setSortDir(1) }
  }

  function arrow(col: SortCol) {
    if (sortCol === col) return <span className={styles.sortActive}>{sortDir === 1 ? '↑' : '↓'}</span>
    return <span className={styles.sortIdle}>⇅</span>
  }

  const generatedStr = useMemo(() => {
    if (!generated) return ''
    try {
      const d = new Date(generated)
      return `Updated ${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
    } catch { return '' }
  }, [generated])

  if (loading) return <div className={styles.loading}><div className={styles.spinner} /><span>Loading catalog…</span></div>
  if (error)   return <div className={styles.error}>Failed to load catalog data: {error}</div>

  return (
    <div className="page-wrap">
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
        <p className="count-label">
          Showing <b>{filtered.length.toLocaleString()}</b> of <b>{packages.length.toLocaleString()}</b> packages
        </p>
        {generatedStr && <p className="generated">{generatedStr}</p>}
      </div>

      <div className="card">
        {filtered.length === 0 ? (
          <div className="empty-state">
            <h3>No packages found</h3>
            <p>Try a different search term.</p>
          </div>
        ) : (
          <div className={styles.tableScroll}><table>
            <thead>
              <tr>
                <th className={styles.thIdx}>#</th>
                <th className={`sortable${sortCol === 'name' ? ' sorted' : ''} ${styles.thPkg}`} onClick={() => handleSort('name')}>
                  Package {arrow('name')}
                </th>
                <th className={styles.thVersions}>Versions</th>
                <th className={`sortable${sortCol === 'cve' ? ' sorted' : ''} ${styles.thCve}`} onClick={() => handleSort('cve')}>
                  Vulnerabilities Summary {arrow('cve')}
                </th>
                <th className={styles.thIndex}>Index</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((pkg, i) => {
                const scan = scanMap.get(pkg.name)
                const vulnCount = scan?.vulns.length ?? null

                return (
                  <tr key={pkg.name}>
                    <td className={styles.idx}>{i + 1}</td>
                    <td className={styles.pkgName}>{pkg.name}</td>
                    <td className={styles.versions}>
                      {pkg.versions.length === 0
                        ? <span className={styles.noVersion}>—</span>
                        : pkg.versions.map((v, vi) => (
                            <VersionPill key={v} version={v} latest={vi === pkg.versions.length - 1} />
                          ))
                      }
                    </td>
                    <td className={styles.cveCell}>
                      {vulnCount === null
                        ? <span className={styles.notScanned}>—</span>
                        : vulnCount === 0
                          ? <span className={styles.clean}>Clean</span>
                          : scan!.vulns.map((v, vi) => {
                              const label = v.cves[0] ?? v.id
                              return <span key={vi} className={styles.vulnId}>{label}</span>
                            })
                      }
                    </td>
                    <td className={styles.indexCell}>
                      {indexUrl && (
                        <a
                          className={styles.indexBtn}
                          href={`${indexUrl}${pkg.name}/`}
                          target="_blank"
                          rel="noopener"
                        >
                          View ↗
                        </a>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table></div>
        )}
      </div>
    </div>
  )
}
