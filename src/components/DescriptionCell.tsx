import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { VersionPill } from './VersionPill'
import { CvePill } from './CvePill'
import styles from './DescriptionCell.module.css'

const TRUNCATE = 90

interface Props {
  text: string
  packageName?: string
  version?: string
  vulnId?: string
  cves?: string[]
  fix?: string[]
}

export function DescriptionCell({ text, packageName, version, vulnId, cves, fix }: Props) {
  const [open, setOpen] = useState(false)
  const short = text.length > TRUNCATE ? text.slice(0, TRUNCATE).trimEnd() + '…' : text
  const hasMore = text.length > TRUNCATE

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <div className={styles.wrap}>
      <span className={styles.short}>{short}</span>
      {hasMore && (
        <>
          <button
            className={`${styles.btn} ${open ? styles.btnActive : ''}`}
            onClick={e => { e.stopPropagation(); setOpen(v => !v) }}
            type="button"
            title="Show full description"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </button>

          {open && createPortal(
            <div className={styles.backdrop} onClick={() => setOpen(false)}>
              <div className={styles.modal} onClick={e => e.stopPropagation()}>

                {/* ── Package context ── */}
                {packageName && (
                  <div className={styles.pkgHeader}>
                    <div className={styles.pkgRow}>
                      <span className={styles.pkgName}>{packageName}</span>
                      {version && <VersionPill version={version} latest />}
                      <button className={styles.closeBtn} onClick={() => setOpen(false)} type="button">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                    {(vulnId || (cves && cves.length > 0)) && (
                      <div className={styles.metaRow}>
                        {vulnId && <span className={styles.vulnId}>{vulnId}</span>}
                        {cves && cves.map(c => <CvePill key={c} id={c} />)}
                      </div>
                    )}
                    {fix && fix.length > 0 && (
                      <div className={styles.fixRow}>
                        <span className={styles.fixLabel}>Fix available:</span>
                        <span className={styles.fixValue}>{fix.join(', ')}</span>
                      </div>
                    )}
                    {fix && fix.length === 0 && (
                      <div className={styles.fixRow}>
                        <span className={styles.noFix}>No fix available</span>
                      </div>
                    )}
                  </div>
                )}

                {/* ── Fallback header when no package context ── */}
                {!packageName && (
                  <div className={styles.modalHeader}>
                    <span className={styles.modalTitle}>Description</span>
                    <button className={styles.closeBtn} onClick={() => setOpen(false)} type="button">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>
                )}

                <p className={styles.modalBody}>{text}</p>
              </div>
            </div>,
            document.body
          )}
        </>
      )}
    </div>
  )
}
