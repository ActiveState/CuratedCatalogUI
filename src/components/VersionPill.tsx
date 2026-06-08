import styles from './VersionPill.module.css'

interface Props {
  version: string
  latest?: boolean
}

export function VersionPill({ version, latest }: Props) {
  return (
    <span className={`${styles.pill} ${latest ? styles.latest : ''}`}>
      {version}
    </span>
  )
}
