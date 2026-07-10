import type { Package, ScannedPackage } from '../types'
import type { Language } from '../languages'

export type ExportDetail = 'catalog' | 'summary' | 'full'

export interface LangExport {
  language: Language
  packages: Package[]
  scanned: ScannedPackage[]
  indexUrl: string
}

export async function buildXlsxBuffer(langs: LangExport[], detail: ExportDetail): Promise<ArrayBuffer> {
  const XLSX = await import('xlsx')
  const wb = XLSX.utils.book_new()

  for (const { language, packages, scanned, indexUrl } of langs) {
    const scanMap = new Map(scanned.map(p => [p.name, p]))
    const hasIndex = Boolean(indexUrl)
    const rows: (string | number)[][] = []

    if (detail === 'catalog') {
      rows.push(['#', 'Package', 'Versions', ...(hasIndex ? ['Index URL'] : [])])
      packages.forEach((pkg, i) =>
        rows.push([i + 1, pkg.name, pkg.versions.join('; '), ...(hasIndex ? [`${indexUrl}${pkg.name}/`] : [])]),
      )
    } else if (detail === 'summary') {
      rows.push(['#', 'Package', 'Versions', 'Vuln Count', 'CVE IDs', ...(hasIndex ? ['Index URL'] : [])])
      packages.forEach((pkg, i) => {
        const sp = scanMap.get(pkg.name)
        rows.push([
          i + 1,
          pkg.name,
          pkg.versions.join('; '),
          sp?.vulns.length ?? 0,
          sp?.vulns.flatMap(v => v.cves).join('; ') ?? '',
          ...(hasIndex ? [`${indexUrl}${pkg.name}/`] : []),
        ])
      })
    } else {
      rows.push(['#', 'Package', 'Version', 'Severity', 'Vuln ID', 'CVE Aliases', 'Fix Version', 'Description'])
      let n = 0
      for (const pkg of packages) {
        const sp = scanMap.get(pkg.name)
        if (!sp || sp.vulns.length === 0) {
          rows.push([++n, pkg.name, sp?.version ?? '', '', '', '', '', ''])
        } else {
          for (const v of sp.vulns) {
            rows.push([++n, pkg.name, sp.version, v.severity ?? '', v.id, v.cves.join('; '), v.fix.join('; '), v.description])
          }
        }
      }
    }

    const ws = XLSX.utils.aoa_to_sheet(rows)

    ws['!views'] = [{ state: 'frozen', xSplit: 0, ySplit: 1 }]

    if (ws['!ref']) {
      const range = XLSX.utils.decode_range(ws['!ref'])
      ws['!autofilter'] = {
        ref: XLSX.utils.encode_range({ s: { r: 0, c: 0 }, e: { r: 0, c: range.e.c } }),
      }
    }

    if (detail === 'catalog') {
      ws['!cols'] = [{ wch: 5 }, { wch: 45 }, { wch: 35 }, ...(hasIndex ? [{ wch: 65 }] : [])]
    } else if (detail === 'summary') {
      ws['!cols'] = [{ wch: 5 }, { wch: 45 }, { wch: 35 }, { wch: 12 }, { wch: 55 }, ...(hasIndex ? [{ wch: 65 }] : [])]
    } else {
      ws['!cols'] = [{ wch: 5 }, { wch: 35 }, { wch: 18 }, { wch: 12 }, { wch: 22 }, { wch: 30 }, { wch: 20 }, { wch: 80 }]
    }

    XLSX.utils.book_append_sheet(wb, ws, language.label)
  }

  return (XLSX.write(wb, { type: 'array', bookType: 'xlsx' }) as Uint8Array).buffer as ArrayBuffer
}

export async function buildAndDownload(
  langs: LangExport[],
  detail: ExportDetail,
  filename: string,
): Promise<void> {
  const buf = await buildXlsxBuffer(langs, detail)
  const blob = new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
