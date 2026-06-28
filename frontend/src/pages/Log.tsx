import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAuditLog } from '../api'
import type { AuditLogFull } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import { formatAuditDetails } from '../utils/auditDetails'
import dayjs from 'dayjs'
import shared from '../styles/shared.module.css'
import styles from './Log.module.css'

export default function Log() {
  const [log, setLog] = useState<AuditLogFull[]>([])
  const { t } = useI18n()

  useEffect(() => { getAuditLog().then(setLog) }, [])

  return (
    <div>
      <h1>{t('log.title')}</h1>
      <table className={styles.table}>
        <thead>
          <tr className={styles.tableHead}>
            <th className={shared.th}>{t('set_detail.history_date')}</th>
            <th className={shared.th}>{t('log.set')}</th>
            <th className={shared.th}>{t('set_detail.history_action')}</th>
            <th className={shared.th}>{t('set_detail.history_user')}</th>
            <th className={shared.th}>{t('set_detail.history_details')}</th>
          </tr>
        </thead>
        <tbody>
          {log.map(h => (
            <tr key={h.id} className={styles.tableRow}>
              <td className={styles.tdNoWrap}>{dayjs(h.created_at).format('DD.MM.YYYY HH:mm')}</td>
              <td className={shared.td}>
                {h.set_id && h.set_name ? (
                  <Link to={`/sets/${h.set_id}`} className={styles.setLink}>{h.set_name}</Link>
                ) : '—'}
              </td>
              <td className={shared.td}>{t(`action.${h.action}` as any) ?? h.action}</td>
              <td className={shared.td}>{h.actor ?? '—'}</td>
              <td className={styles.tdMuted}>{formatAuditDetails(h.details, t)}</td>
            </tr>
          ))}
          {log.length === 0 && (
            <tr><td colSpan={5} className={styles.noData}>{t('common.no_data')}</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
