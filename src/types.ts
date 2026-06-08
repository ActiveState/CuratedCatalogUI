export interface Package {
  name: string
  versions: string[]
}

export interface CatalogData {
  generated: string
  packages: Package[]
}

export interface Vuln {
  id: string
  cves: string[]
  fix: string[]
  description: string
}

export interface ScannedPackage {
  name: string
  version: string
  vulns: Vuln[]
}
