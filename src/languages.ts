export interface Language {
  id: string
  label: string
  icon: string
  hasIndexUrl: boolean
  scanTool: string
  disabled?: boolean
}

export const LANGUAGES: Language[] = [
  { id: 'python',     label: 'Python',     icon: '🐍', hasIndexUrl: true,  scanTool: 'pip-audit · OSV'    },
  { id: 'javascript', label: 'JavaScript', icon: '🟨', hasIndexUrl: false, scanTool: 'osv-scanner · OSV'  },
  { id: 'java',       label: 'Java',       icon: '☕', hasIndexUrl: false, scanTool: 'osv-scanner · OSV',  disabled: true },
  { id: 'go',         label: 'Go',         icon: '🐹', hasIndexUrl: false, scanTool: 'osv-scanner · OSV',  disabled: true },
  { id: 'rust',       label: 'Rust',       icon: '🦀', hasIndexUrl: false, scanTool: 'osv-scanner · OSV',  disabled: true },
  { id: 'php',        label: 'PHP',        icon: '🐘', hasIndexUrl: false, scanTool: 'osv-scanner · OSV',  disabled: true },
  { id: 'dotnet',     label: 'C#/.NET',    icon: '🔷', hasIndexUrl: false, scanTool: 'osv-scanner · OSV',  disabled: true },
  { id: 'r',          label: 'R',          icon: '📊', hasIndexUrl: false, scanTool: 'osv-scanner · OSV',  disabled: true },
  { id: 'cpp',        label: 'C/C++',      icon: '⚙️', hasIndexUrl: false, scanTool: 'osv-scanner · OSV',  disabled: true },
]

export function getLanguage(id: string): Language {
  return LANGUAGES.find(l => l.id === id) ?? LANGUAGES[0]
}
