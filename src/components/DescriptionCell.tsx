import styles from './DescriptionCell.module.css'

const TRUNCATE = 90

interface Props {
  text: string
}

export function DescriptionCell({ text }: Props) {
  const short = text.length > TRUNCATE ? text.slice(0, TRUNCATE).trimEnd() + '…' : text
  const hasMore = text.length > TRUNCATE

  return (
    <div className={styles.wrap}>
      <span className={styles.short}>{short}</span>
      {hasMore && (
        <span className={styles.tipWrap}>
          <button className={styles.btn} tabIndex={0} type="button">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </button>
          <div className={styles.tooltip}>
            <div className={styles.tooltipInner}>{text}</div>
          </div>
        </span>
      )}
    </div>
  )
}
