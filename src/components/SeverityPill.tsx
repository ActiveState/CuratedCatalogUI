import styles from './SeverityPill.module.css'

const LABELS: Record<string, string> = {
  CRITICAL: 'Critical',
  HIGH:     'High',
  MODERATE: 'Moderate',
  LOW:      'Low',
}

interface Props {
  severity?: string | null
}

export function SeverityPill({ severity }: Props) {
  if (!severity) return <span className={styles.unknown}>—</span>
  const key   = severity.toUpperCase()
  const label = LABELS[key] ?? severity
  const cls   = styles[key.toLowerCase() as keyof typeof styles] ?? styles.unknown
  return <span className={`${styles.pill} ${cls}`}>{label}</span>
}
