import { useEffect, useRef, useState } from 'react'
import { useCustomer } from '../context/CustomerContext'
import { LANGUAGES, getLanguage } from '../languages'
import { fetchLanguageData } from '../hooks/useLanguageData'
import type { Package, ScannedPackage } from '../types'
import type { ExportDetail, LangExport } from '../utils/buildExport'
import styles from './ExportDropdown.module.css'

interface Props {
  currentLang: string
  packages: Package[]
  scanned: ScannedPackage[]
  generated: string
  indexUrl: string
}

const googleEnabled = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID)

export function ExportDropdown({ currentLang, packages, scanned, generated, indexUrl }: Props) {
  const { customerId } = useCustomer()
  const [open, setOpen] = useState(false)
  const [scope, setScope] = useState<'current' | 'all'>('current')
  const [detail, setDetail] = useState<ExportDetail>('catalog')
  const [downloading, setDownloading] = useState(false)
  const [sheetsState, setSheetsState] = useState<'idle' | 'uploading' | 'error'>('idle')
  const wrapRef = useRef<HTMLDivElement>(null)

  // Pre-warm dependencies when the panel opens
  useEffect(() => {
    if (!open) return
    import('../utils/buildExport')
    if (googleEnabled) import('../utils/googleDrive').then(m => m.preloadGSI().catch(() => {}))
  }, [open])

  useEffect(() => {
    if (!open) return
    function handler(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  async function resolveLangs(): Promise<LangExport[]> {
    if (scope === 'current') {
      return [{ language: getLanguage(currentLang), packages, scanned, indexUrl }]
    }
    const base = import.meta.env.BASE_URL
    const results = await Promise.allSettled(
      LANGUAGES.map(lang =>
        fetchLanguageData(base, customerId, lang.id).then(d => ({
          language: lang,
          packages: d.packages,
          scanned: d.scanned,
          indexUrl: d.indexUrl,
        })),
      ),
    )
    return results
      .filter((r): r is PromiseFulfilledResult<LangExport> => r.status === 'fulfilled' && r.value.packages.length > 0)
      .map(r => r.value)
  }

  function makeFilename(scopeSlug: string) {
    const date = generated
      ? new Date(generated).toISOString().split('T')[0]
      : new Date().toISOString().split('T')[0]
    return `${customerId}-${scopeSlug}-catalog-${date}.xlsx`
  }

  async function handleDownload() {
    setDownloading(true)
    try {
      const { buildAndDownload } = await import('../utils/buildExport')
      const langs = await resolveLangs()
      await buildAndDownload(langs, detail, makeFilename(scope === 'current' ? currentLang : 'all'))
      setOpen(false)
    } finally {
      setDownloading(false)
    }
  }

  async function handleOpenInSheets() {
    setSheetsState('uploading')
    try {
      const [{ buildXlsxBuffer }, { openInSheets }] = await Promise.all([
        import('../utils/buildExport'),
        import('../utils/googleDrive'),
      ])
      const langs = await resolveLangs()
      const buf = await buildXlsxBuffer(langs, detail)
      await openInSheets(buf, makeFilename(scope === 'current' ? currentLang : 'all'))
      setOpen(false)
    } catch (err) {
      setSheetsState('error')
      setTimeout(() => setSheetsState('idle'), 3000)
    }
  }

  const currentLabel = getLanguage(currentLang).label

  return (
    <div className={styles.wrap} ref={wrapRef}>
      <button className={styles.trigger} onClick={() => setOpen(o => !o)} aria-haspopup="true" aria-expanded={open}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Export
      </button>

      {open && (
        <div className={styles.panel}>
          <div className={styles.group}>
            <div className={styles.groupLabel}>Languages</div>
            <label className={styles.option}>
              <input type="radio" checked={scope === 'current'} onChange={() => setScope('current')} />
              {currentLabel} only
            </label>
            <label className={styles.option}>
              <input type="radio" checked={scope === 'all'} onChange={() => setScope('all')} />
              All languages
            </label>
          </div>

          <div className={styles.divider} />

          <div className={styles.group}>
            <div className={styles.groupLabel}>Detail</div>
            <label className={styles.option}>
              <input type="radio" checked={detail === 'catalog'} onChange={() => setDetail('catalog')} />
              Catalog only
            </label>
            <label className={styles.option}>
              <input type="radio" checked={detail === 'summary'} onChange={() => setDetail('summary')} />
              Catalog + CVE summary
            </label>
            <label className={styles.option}>
              <input type="radio" checked={detail === 'full'} onChange={() => setDetail('full')} />
              Full CVE rows
            </label>
          </div>

          <div className={styles.divider} />

          <div className={styles.actions}>
            <button className={styles.downloadBtn} onClick={handleDownload} disabled={downloading}>
              {downloading ? 'Generating…' : '↓ Download .xlsx'}
            </button>
            {googleEnabled && (
              <button
                className={`${styles.sheetsBtn}${sheetsState === 'error' ? ` ${styles.sheetsBtnError}` : ''}`}
                onClick={handleOpenInSheets}
                disabled={sheetsState === 'uploading'}
              >
                {sheetsState === 'uploading' ? 'Uploading…' : sheetsState === 'error' ? 'Auth failed — retry?' : (
                  <>
                    <SheetsIcon />
                    Open in Sheets
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function SheetsIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="3" width="7" height="7" rx="1" fill="currentColor" opacity=".7"/>
      <rect x="14" y="3" width="7" height="7" rx="1" fill="currentColor" opacity=".7"/>
      <rect x="3" y="14" width="7" height="7" rx="1" fill="currentColor" opacity=".7"/>
      <rect x="14" y="14" width="7" height="7" rx="1" fill="currentColor" opacity=".7"/>
    </svg>
  )
}
