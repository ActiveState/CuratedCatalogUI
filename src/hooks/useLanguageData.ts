import { useEffect, useState } from 'react'
import type { Package, ScannedPackage } from '../types'
import { useCustomer } from '../context/CustomerContext'

export interface LanguageData {
  packages: Package[]
  scanned: ScannedPackage[]
  generated: string
  indexUrl: string
  loading: boolean
  error: string | null
}

const EMPTY: LanguageData = { packages: [], scanned: [], generated: '', indexUrl: '', loading: true, error: null }

// Module-level cache keyed by "customerId/lang"
const cache = new Map<string, LanguageData>()

export function useLanguageData(lang: string): LanguageData {
  const { customerId } = useCustomer()
  const cacheKey = `${customerId}/${lang}`

  const [data, setData] = useState<LanguageData>(() => cache.get(cacheKey) ?? EMPTY)

  useEffect(() => {
    if (cache.has(cacheKey)) {
      setData(cache.get(cacheKey)!)
      return
    }
    setData(EMPTY)
    const base = import.meta.env.BASE_URL
    Promise.all([
      fetch(`${base}data/${customerId}/${lang}/catalog.json`).then(r => r.json()),
      fetch(`${base}data/${customerId}/${lang}/audit.json`).then(r => r.json()),
    ])
      .then(([catalog, audit]) => {
        const packages: Package[] = catalog.packages ?? catalog
        const generated: string  = catalog.generated ?? ''
        const indexUrl: string   = catalog.index_url ?? ''

        const rawDeps: any[] = Array.isArray(audit) ? audit : (audit.dependencies ?? [])
        const scanned: ScannedPackage[] = rawDeps
          .filter((dep: any) => !dep.skip_reason)
          .map((dep: any) => ({
            name:    dep.name,
            version: dep.version ?? '',
            vulns:   (dep.vulns ?? []).map((v: any) => ({
              id:          v.id ?? '',
              cves:        (v.aliases ?? v.cves ?? []).filter((a: string) => a.startsWith('CVE-')),
              fix:         v.fix_versions ?? v.fix ?? [],
              description: v.description ?? '',
            })),
          }))

        const result: LanguageData = { packages, scanned, generated, indexUrl, loading: false, error: null }
        cache.set(cacheKey, result)
        setData(result)
      })
      .catch(err => {
        const result: LanguageData = { packages: [], scanned: [], generated: '', indexUrl: '', loading: false, error: err.message }
        setData(result)
      })
  }, [customerId, lang, cacheKey])

  return data
}
