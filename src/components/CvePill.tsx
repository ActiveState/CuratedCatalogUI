import styles from './CvePill.module.css'

export function CvePill({ id }: { id: string }) {
  return <span className={styles.pill}>{id}</span>
}
