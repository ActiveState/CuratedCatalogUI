import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { CatalogPage } from './pages/CatalogPage'
import { ScanReportPage } from './pages/ScanReportPage'
import { PackageDetailPage } from './pages/PackageDetailPage'

export default function App() {
  return (
    <HashRouter>
      <Navbar />
      <Routes>
        <Route path="/"                          element={<Navigate to="/python" replace />} />
        <Route path="/:lang"                     element={<CatalogPage />} />
        <Route path="/:lang/cve-report"          element={<ScanReportPage />} />
        <Route path="/:lang/package/:name"       element={<PackageDetailPage />} />
      </Routes>
    </HashRouter>
  )
}
