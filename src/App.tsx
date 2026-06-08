import { HashRouter, Routes, Route } from 'react-router-dom'
import { DataProvider } from './context/DataContext'
import { Navbar } from './components/Navbar'
import { CatalogPage } from './pages/CatalogPage'
import { ScanReportPage } from './pages/ScanReportPage'
import { PackageDetailPage } from './pages/PackageDetailPage'

export default function App() {
  return (
    <DataProvider>
      <HashRouter>
        <Navbar />
        <Routes>
          <Route path="/"                  element={<CatalogPage />} />
          <Route path="/cve-report"        element={<ScanReportPage />} />
          <Route path="/package/:name"     element={<PackageDetailPage />} />
        </Routes>
      </HashRouter>
    </DataProvider>
  )
}
