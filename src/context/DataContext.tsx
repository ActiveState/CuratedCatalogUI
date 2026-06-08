import { createContext, useContext, useEffect, useState } from 'react'
import type { Package, ScannedPackage } from '../types'

interface DataContextValue {
  packages: Package[]
  scanned: ScannedPackage[]
  generated: string
  indexUrl: string
  loading: boolean
  error: string | null
}

const DataContext = createContext<DataContextValue>({
  packages: [], scanned: [], generated: '', indexUrl: '', loading: true, error: null,
})

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [packages, setPackages] = useState<Package[]>([])
  const [scanned, setScanned] = useState<ScannedPackage[]>([])
  const [generated, setGenerated] = useState('')
  const [indexUrl, setIndexUrl] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const base = import.meta.env.BASE_URL
    Promise.all([
      fetch(`${base}data/catalog.json`).then(r => r.json()),
      fetch(`${base}data/audit.json`).then(r => r.json()),
    ])
      .then(([catalog, audit]) => {
        setPackages(catalog.packages ?? catalog)
        setGenerated(catalog.generated ?? '')
        setIndexUrl(catalog.index_url ?? '')
        setScanned(Array.isArray(audit) ? audit : (audit.dependencies ?? []))
        setLoading(false)
      })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  return (
    <DataContext.Provider value={{ packages, scanned, generated, indexUrl, loading, error }}>
      {children}
    </DataContext.Provider>
  )
}

export const useData = () => useContext(DataContext)
