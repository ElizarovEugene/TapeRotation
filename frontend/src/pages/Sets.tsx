import { useEffect, useState, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { getSets, deleteSet, markReturned, getLocations } from '../api'
import type { TapeSet, SetStatus, Location } from '../api/types'
import StatusBadge from '../components/StatusBadge'
import { useI18n } from '../i18n/I18nContext'
import dayjs from 'dayjs'
import SetModal from './SetModal'
import { useAuth } from '../auth/AuthContext'
import shared from '../styles/shared.module.css'
import styles from './Sets.module.css'

type SortField = 'id' | 'recording_date' | 'expires_at'
type SortDir = 'asc' | 'desc'

export default function Sets() {
  const { user } = useAuth()
  const { t } = useI18n()
  const canWrite = user?.role !== 'readonly'
  const [sets, setSets] = useState<TapeSet[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [statusFilter, setStatusFilter] = useState<SetStatus | ''>('')
  const [locationFilter, setLocationFilter] = useState<number | ''>('')
  const [search, setSearch] = useState('')
  const [sortField, setSortField] = useState<SortField>('id')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<TapeSet | null>(null)

  const load = useCallback(() => {
    getSets().then(setSets)
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => { getLocations().then(setLocations) }, [])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('asc')
    }
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    let result = sets
    if (statusFilter) result = result.filter(s => s.status === statusFilter)
    if (locationFilter !== '') result = result.filter(s => s.location_id === locationFilter)
    if (q) result = result.filter(s =>
      s.tapes.some(tp => tp.label.toLowerCase().includes(q)) ||
      (s.notes ?? '').toLowerCase().includes(q)
    )
    return [...result].sort((a, b) => {
      let av: string | number, bv: string | number
      if (sortField === 'id') { av = a.id; bv = b.id }
      else if (sortField === 'recording_date') { av = a.recording_date ?? ''; bv = b.recording_date ?? '' }
      else { av = a.expires_at ?? ''; bv = b.expires_at ?? '' }
      if (av < bv) return sortDir === 'asc' ? -1 : 1
      if (av > bv) return sortDir === 'asc' ? 1 : -1
      return 0
    })
  }, [sets, statusFilter, locationFilter, search, sortField, sortDir])

  const handleDelete = async (id: number) => {
    if (!confirm(t('sets.delete_confirm'))) return
    await deleteSet(id)
    load()
  }

  const handleReturn = async (id: number) => {
    if (!confirm(t('sets.return_confirm'))) return
    await markReturned(id)
    load()
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <span className={styles.sortIconInactive}>↕</span>
    return <span className={styles.sortIconActive}>{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <div>
      <div className={shared.pageHeader}>
        <h1>{t('sets.title')}</h1>
        <div className={styles.headerActions}>
          {canWrite && (
            <button onClick={() => { setEditing(null); setShowModal(true) }} className={shared.btnPrimary}>
              {t('sets.add_set')}
            </button>
          )}
        </div>
      </div>

      <div className={styles.searchRow}>
        <input
          className={styles.searchInput}
          placeholder={t('sets.search_placeholder')}
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className={styles.filterRow}>
        <div className={styles.filterBtnGroup}>
          {(['', 'in_storage', 'expired', 'returned'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={statusFilter === s ? styles.btnFilterActive : styles.btnFilter}
            >
              {s === '' ? t('sets.all_statuses') : t(`status.${s}` as any)}
            </button>
          ))}
        </div>

        <select
          className={styles.selectFilter}
          value={locationFilter}
          onChange={e => setLocationFilter(e.target.value === '' ? '' : Number(e.target.value))}
        >
          <option value="">{t('sets.all_locations')}</option>
          {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
        </select>

        {(statusFilter || locationFilter !== '' || search) && (
          <button
            className={styles.btnFilterClear}
            onClick={() => { setStatusFilter(''); setLocationFilter(''); setSearch('') }}
          >
            {t('sets.clear_filters')}
          </button>
        )}
      </div>

      <table className={styles.table}>
        <thead>
          <tr className={styles.tableHead}>
            <th className={styles.thSortable} onClick={() => handleSort('id')}>
              {t('dashboard.set')} <SortIcon field="id" />
            </th>
            <th className={shared.th}>{t('common.location')}</th>
            <th className={styles.thSortable} onClick={() => handleSort('recording_date')}>
              {t('sets.recording_date')} <SortIcon field="recording_date" />
            </th>
            <th className={styles.thSortable} onClick={() => handleSort('expires_at')}>
              {t('sets.expires')} <SortIcon field="expires_at" />
            </th>
            <th className={shared.th}>{t('sets.tapes_count')}</th>
            <th className={shared.th}>{t('common.status')}</th>
            <th className={shared.th}>{t('common.actions')}</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map(s => (
            <tr key={s.id} className={styles.tableRow}>
              <td className={shared.td}><Link to={`/sets/${s.id}`} className={styles.link}>{s.name}</Link></td>
              <td className={shared.td}>{s.location?.name ?? '—'}</td>
              <td className={shared.td}>{s.recording_date ? dayjs(s.recording_date).format('DD.MM.YYYY') : '—'}</td>
              <td className={shared.td}>
                {s.retention_forever ? <span title="Forever" className={styles.foreverIcon}>∞</span>
                  : s.expires_at ? dayjs(s.expires_at).format('DD.MM.YYYY') : '—'}
              </td>
              <td className={shared.td}>{s.tapes.length}</td>
              <td className={shared.td}><StatusBadge status={s.status} /></td>
              <td className={shared.td}>
                {canWrite && <>
                  <button onClick={() => { setEditing(s); setShowModal(true) }} className={shared.btnSm}>{t('common.edit')}</button>
                  {s.status !== 'returned' && (
                    <button onClick={() => handleReturn(s.id)} className={styles.btnSmReturn}>{t('common.return')}</button>
                  )}
                  <button onClick={() => handleDelete(s.id)} className={styles.btnSmDelete}>{t('common.delete')}</button>
                </>}
              </td>
            </tr>
          ))}
          {filtered.length === 0 && (
            <tr><td colSpan={7} className={styles.noData}>{t('common.no_data')}</td></tr>
          )}
        </tbody>
      </table>

      {showModal && (
        <SetModal
          set={editing}
          locations={locations}
          existingNames={[...new Set(sets.map(s => s.name))]}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); load() }}
        />
      )}
    </div>
  )
}
