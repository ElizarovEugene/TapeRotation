import type { SetStatus } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import styles from './StatusBadge.module.css'

export default function StatusBadge({ status }: { status: SetStatus }) {
  const { t } = useI18n()
  const label = t(`status.${status}` as any)
  return (
    <span className={`${styles.badge} ${styles[status]}`}>
      {label}
    </span>
  )
}
