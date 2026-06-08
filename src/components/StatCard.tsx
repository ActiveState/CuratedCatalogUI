import styles from './StatCard.module.css'

type Variant = 'default' | 'blue' | 'red' | 'amber' | 'green'

interface Props {
  label: string
  value: number | string
  variant?: Variant
}

export function StatCard({ label, value, variant = 'default' }: Props) {
  return (
    <div className={`${styles.card} ${styles[variant]}`}>
      <div className={styles.label}>{label}</div>
      <div className={styles.value}>{typeof value === 'number' ? value.toLocaleString() : value}</div>
    </div>
  )
}
