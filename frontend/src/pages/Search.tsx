import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { searchTapes } from '../api'
import type { TapeSearchResult } from '../api/types'
import StatusBadge from '../components/StatusBadge'
import { useI18n } from '../i18n/I18nContext'
import dayjs from 'dayjs'
import shared from '../styles/shared.module.css'
import styles from './Search.module.css'

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<TapeSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const { t } = useI18n()
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSearch = async () => {
    const q = query.trim()
    if (!q) return
    setLoading(true)
    try {
      const res = await searchTapes(q)
      setResults(res)
      setSearched(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className={styles.title}>{t('search.title')}</h1>

      <div className={styles.searchRow}>
        <input
          ref={inputRef}
          className={styles.searchInput}
          placeholder={t('search.placeholder')}
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          autoFocus
        />
        <button className={shared.btnPrimary} onClick={handleSearch} disabled={loading || !query.trim()}>
          {loading ? t('search.searching') : t('search.button')}
        </button>
      </div>

      {searched && (
        results.length === 0 ? (
          <p className={styles.notFound}>{t('search.not_found', { q: query })}</p>
        ) : (
          <>
            <p className={styles.found}>
              {t('search.found')} {results.length}
            </p>
            <table className={styles.table}>
              <thead>
                <tr className={styles.tableHead}>
                  <th className={shared.th}>{t('search.tape_label')}</th>
                  <th className={shared.th}>{t('search.lto_version')}</th>
                  <th className={shared.th}>{t('search.set')}</th>
                  <th className={shared.th}>{t('search.set_status')}</th>
                  <th className={shared.th}>{t('search.recording_date')}</th>
                  <th className={shared.th}>{t('search.expires')}</th>
                </tr>
              </thead>
              <tbody>
                {results.map(r => (
                  <tr key={r.tape_id} className={styles.tableRow}>
                    <td className={styles.tdMono}>{r.tape_label}</td>
                    <td className={r.tape_lto_version ? styles.tdLtoBlue : styles.tdLtoMuted}>
                      {r.tape_lto_version ?? '—'}
                    </td>
                    <td className={shared.td}>
                      {r.set_id ? (
                        <Link to={`/sets/${r.set_id}`} className={styles.link}>{r.set_name}</Link>
                      ) : '—'}
                    </td>
                    <td className={shared.td}>
                      {r.set_status ? <StatusBadge status={r.set_status} /> : '—'}
                    </td>
                    <td className={shared.td}>{r.recording_date ? dayjs(r.recording_date).format('DD.MM.YYYY') : '—'}</td>
                    <td className={shared.td}>{r.expires_at ? dayjs(r.expires_at).format('DD.MM.YYYY') : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )
      )}
    </div>
  )
}
