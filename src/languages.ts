export interface Language {
  id: string
  label: string
  icon: string
  hasIndexUrl: boolean
  scanTool: string
  disabled?: boolean
}

const base = import.meta.env.BASE_URL
export const LANGUAGES: Language[] = [
  { id: 'python',     label: 'Python',     icon: `${base}icons/python.svg`,     hasIndexUrl: true,  scanTool: 'pip-audit · OSV'   },
  { id: 'javascript', label: 'JavaScript', icon: `${base}icons/javascript.svg`, hasIndexUrl: false, scanTool: 'osv-scanner · OSV' },
  { id: 'java',       label: 'Java',       icon: `${base}icons/java.svg`,       hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'go',         label: 'Go',         icon: `${base}icons/go.svg`,         hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'rust',       label: 'Rust',       icon: `${base}icons/rust.svg`,       hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'php',        label: 'PHP',        icon: `${base}icons/php.svg`,        hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'dotnet',     label: 'C#/.NET',    icon: `${base}icons/dotnet.svg`,     hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'r',          label: 'R',          icon: `${base}icons/r.svg`,          hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
  { id: 'cpp',        label: 'C/C++',      icon: `${base}icons/cpp.svg`,        hasIndexUrl: false, scanTool: 'osv-scanner · OSV', disabled: true },
]

export function getLanguage(id: string): Language {
  return LANGUAGES.find(l => l.id === id) ?? LANGUAGES[0]
}
