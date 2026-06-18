import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { VersionPill } from './VersionPill'
import { CvePill } from './CvePill'
import { SeverityPill } from './SeverityPill'
import { MarkdownText } from './MarkdownText'
import type { Vuln } from '../types'
import styles from './DescriptionCell.module.css'

const TRUNCATE = 90

interface Props {
  text: string          // current vuln description — used for row preview
  packageName?: string
  version?: string
  allVulns?: Vuln[]     // all vulns for this package
  vulnIndex?: number    // which one this row represents
}

export function DescriptionCell({ text, packageName, version, allVulns, vulnIndex = 0 }: Props) {
  const [open, setOpen]       = useState(false)
  const [activeIdx, setActive] = useState(vulnIndex)
  const bodyRef = useRef<HTMLDivElement>(null)

  // reset to the row's own vuln each time the modal opens
  useEffect(() => { if (open) setActive(vulnIndex) }, [open, vulnIndex])

  // scroll body back to top when switching between vulns
  useEffect(() => { if (bodyRef.current) bodyRef.current.scrollTop = 0 }, [activeIdx])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  const short    = text.length > TRUNCATE ? text.slice(0, TRUNCATE).trimEnd() + '…' : text
  const hasMore  = text.length > 0
  const current  = allVulns?.[activeIdx]
  const hasMulti = (allVulns?.length ?? 0) > 1

  // detect duplicate IDs so we can label them
  const idCount: Record<string, number> = {}
  allVulns?.forEach(v => { idCount[v.id] = (idCount[v.id] ?? 0) + 1 })
  const idOccurrence: Record<number, number> = {}
  allVulns?.forEach((v, i) => {
    const seen = allVulns.slice(0, i).filter(x => x.id === v.id).length
    idOccurrence[i] = seen
  })

  function pillLabel(v: Vuln, i: number) {
    return idCount[v.id] > 1 ? `${v.id} (${idOccurrence[i] + 1})` : v.id
  }

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

                <div className={styles.pkgHeader}>
                  {/* package name + version + close */}
                  <div className={styles.pkgRow}>
                    <span className={styles.pkgName}>{packageName}</span>
                    {version && <VersionPill version={version} latest />}
                    <button className={styles.closeBtn} onClick={() => setOpen(false)} type="button">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>

                  {/* vuln ID pills — clickable when multiple */}
                  {allVulns && allVulns.length > 0 && (
                    <div className={styles.vulnPills}>
                      {allVulns.map((v, i) => (
                        <button
                          key={i}
                          className={`${styles.vulnPill} ${i === activeIdx ? styles.vulnPillActive : ''}`}
                          onClick={() => setActive(i)}
                          type="button"
                          title={hasMulti ? `Switch to vulnerability ${i + 1}` : undefined}
                        >
                          {pillLabel(v, i)}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* severity + CVE aliases for active vuln */}
                  {current && (current.severity || current.cves.length > 0) && (
                    <div className={styles.metaRow}>
                      {current.severity && <SeverityPill severity={current.severity} />}
                      {current.cves.map(c => <CvePill key={c} id={c} />)}
                    </div>
                  )}

                  {/* fix version for active vuln */}
                  {current && (
                    <div className={styles.fixRow}>
                      {current.fix.length > 0
                        ? <><span className={styles.fixLabel}>Fix available:</span><span className={styles.fixValue}>{current.fix.join(', ')}</span></>
                        : <span className={styles.noFix}>No fix available</span>
                      }
                    </div>
                  )}
                </div>

                <div className={styles.modalBody} ref={bodyRef}>
                  <MarkdownText text={current?.description ?? text} />
                </div>
              </div>
            </div>,
            document.body
          )}
        </>
      )}
    </div>
  )
}
