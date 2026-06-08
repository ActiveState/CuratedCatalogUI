import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useData } from '../context/DataContext'
import { VersionPill } from '../components/VersionPill'
import styles from './CatalogPage.module.css'

type SortCol = 'name' | 'count'

export function CatalogPage() {
  const { packages, generated, loading, error } = useData()
  const [query, setQuery] = useState('')
  const [sortCol, setSortCol] = useState<SortCol>('name')
  const [sortDir, setSortDir] = useState<1 | -1>(1)

  const filtered = useMemo(() => {
    const q = query.toLowerCase()
    let res = q ? packages.filter(p => p.name.toLowerCase().includes(q)) : packages
    return [...res].sort((a, b) => {
      const av = sortCol === 'name' ? a.name.toLowerCase() : a.versions.length
      const bv = sortCol === 'name' ? b.name.toLowerCase() : b.versions.length
      return av < bv ? -sortDir : av > bv ? sortDir : 0
    })
  }, [packages, query, sortCol, sortDir])

  function handleSort(col: SortCol) {
    if (sortCol === col) setSortDir(d => (d === 1 ? -1 : 1))
    else { setSortCol(col); setSortDir(1) }
  }

  function arrow(col: SortCol) {
    if (sortCol !== col) return null
    return <span className={styles.arrow}>{sortDir === 1 ? '↑' : '↓'}</span>
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
          <table>
            <thead>
              <tr>
                <th style={{ width: 48 }}>#</th>
                <th className={`sortable${sortCol === 'name' ? ' sorted' : ''}`} onClick={() => handleSort('name')}>
                  Package {arrow('name')}
                </th>
                <th className={`sortable${sortCol === 'count' ? ' sorted' : ''}`} onClick={() => handleSort('count')} style={{ width: 80, textAlign: 'center' }}>
                  Count {arrow('count')}
                </th>
                <th>Versions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((pkg, i) => (
                <tr key={pkg.name}>
                  <td className={styles.idx}>{i + 1}</td>
                  <td className={styles.pkgName}>
                    <Link to={`/package/${encodeURIComponent(pkg.name)}`}>{pkg.name}</Link>
                  </td>
                  <td className={styles.idx} style={{ textAlign: 'center' }}>{pkg.versions.length}</td>
                  <td>
                    {pkg.versions.length === 0
                      ? <span className={styles.noVersion}>—</span>
                      : pkg.versions.map((v, vi) => (
                          <VersionPill key={v} version={v} latest={vi === pkg.versions.length - 1} />
                        ))
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
