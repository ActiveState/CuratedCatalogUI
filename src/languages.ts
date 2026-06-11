export interface Language {
  id: string
  label: string
  icon: string
  hasIndexUrl: boolean
  scanTool: string
  disabled?: boolean
}

export const LANGUAGES: Language[] = [
  { id: 'python',     label: 'Python',     icon: '/CuratedCatalogUI/icons/python.svg',     hasIndexUrl: true,  scanTool: 'pip-audit · OSV'   },
  { id: 'javascript', label: 'JavaScript', icon: '/CuratedCatalogUI/icons/javascript.svg', hasIndexUrl: false, scanTool: 'osv-scanner · OSV' },
  { id: 'java',       label: 'Java',       icon: '/CuratedCatalogUI/icons/java.svg',       hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'go',         label: 'Go',         icon: '/CuratedCatalogUI/icons/go.svg',         hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'rust',       label: 'Rust',       icon: '/CuratedCatalogUI/icons/rust.svg',       hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'php',        label: 'PHP',        icon: '/CuratedCatalogUI/icons/php.svg',        hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'dotnet',     label: 'C#/.NET',    icon: '/CuratedCatalogUI/icons/dotnet.svg',     hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'r',          label: 'R',          icon: '/CuratedCatalogUI/icons/r.svg',          hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'cpp',        label: 'C/C++',      icon: '/CuratedCatalogUI/icons/cpp.svg',        hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
]

export function getLanguage(id: string): Language {
  return LANGUAGES.find(l => l.id === id) ?? LANGUAGES[0]
}
