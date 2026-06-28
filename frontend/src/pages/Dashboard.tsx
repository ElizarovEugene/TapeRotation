import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStats, getExpiredSets, getExpiringSets } from '../api'
import type { Stats, TapeSet } from '../api/types'
import StatusBadge from '../components/StatusBadge'
import { useI18n } from '../i18n/I18nContext'
import dayjs from 'dayjs'
import styles from './Dashboard.module.css'
import shared from '../styles/shared.module.css'

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [expired, setExpired] = useState<TapeSet[]>([])
  const [expiring, setExpiring] = useState<TapeSet[]>([])
  const { t } = useI18n()

  useEffect(() => {
    getStats().then(setStats)
    getExpiredSets().then(setExpired)
    getExpiringSets(7).then(setExpiring)
  }, [])

  return (
    <div>
      <h1 className={styles.title}>{t('dashboard.title')}</h1>

      {stats && (
        <div className={styles.statsRow}>
          <StatCard label={t('dashboard.total_sets')} value={stats.total_sets} color="#1a5fa8" />
          <StatCard label={t('dashboard.in_storage')} value={stats.in_storage} color="#0369a1" />
          <StatCard label={t('dashboard.expired')} value={stats.expired} color="#b91c1c" alert={stats.expired > 0} />
          <StatCard label={t('dashboard.expiring_soon')} value={stats.expiring_soon} color="#92400e" alert={stats.expiring_soon > 0} />
          <StatCard label={t('dashboard.returned')} value={stats.returned} color="#166534" />
        </div>
      )}

      {expired.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitleExpired}>{t('dashboard.ready_to_return')}</h2>
          <SetsTable sets={expired} />
        </section>
      )}

      {expiring.length > 0 && (
        <section>
          <h2 className={styles.sectionTitleExpiring}>{t('dashboard.expiring_in_days', { days: 7 })}</h2>
          <SetsTable sets={expiring} />
        </section>
      )}

      {expired.length === 0 && expiring.length === 0 && stats && (
        <p className={styles.noUrgent}>{t('dashboard.no_urgent')}</p>
      )}
    </div>
  )
}

function StatCard({ label, value, color, alert }: { label: string; value: number; color: string; alert?: boolean }) {
  return (
    <div className={[styles.statCard, alert ? styles.statCardAlert : ''].join(' ')}>
      <div className={styles.statValue} style={{ color }}>{value}</div>
      <div className={styles.statLabel}>{label}</div>
    </div>
  )
}

function SetsTable({ sets }: { sets: TapeSet[] }) {
  const { t } = useI18n()
  return (
    <table className={styles.table}>
      <thead>
        <tr className={styles.tableHead}>
          <th className={shared.th}>{t('dashboard.set')}</th>
          <th className={shared.th}>{t('common.location')}</th>
          <th className={shared.th}>{t('dashboard.expires')}</th>
          <th className={shared.th}>{t('dashboard.tapes')}</th>
          <th className={shared.th}>{t('common.status')}</th>
        </tr>
      </thead>
      <tbody>
        {sets.map(s => (
          <tr key={s.id} className={styles.tableRow}>
            <td className={shared.td}><Link to={`/sets/${s.id}`} className={styles.link}>{s.name}</Link></td>
            <td className={shared.td}>{s.location?.name ?? '—'}</td>
            <td className={shared.td}>
              {s.retention_forever ? '∞' : s.expires_at ? dayjs(s.expires_at).format('DD.MM.YYYY') : '—'}
            </td>
            <td className={shared.td}>{s.tapes.length}</td>
            <td className={shared.td}><StatusBadge status={s.status} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
