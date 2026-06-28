import { useEffect, useRef, useState } from 'react'
import { getLocations, importPreview, importExecute } from '../api'
import type { ImportedSet, ImportResult, Location } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import shared from '../styles/shared.module.css'
import styles from './Import.module.css'
import { LTO_OPTIONS } from '../constants'
import DateInput from '../components/DateInput'
import { guessDateFromText } from '../utils/parseDate'

type Format = 'acronis' | 'bareos' | 'commvault' | 'networker' | 'tsm' | 'dataprotector' | 'veeam' | 'backupexec' | 'netbackup' | 'vinchin' | 'kiberbackup'

const FORMAT_LABELS: Record<Format, string> = {
  acronis:       'Acronis Cyber Backup',
  bareos:        'Bareos / Bacula',
  commvault:     'Commvault',
  networker:     'Dell EMC NetWorker',
  tsm:           'IBM Spectrum Protect (TSM)',
  dataprotector: 'OpenText Data Protector',
  veeam:         'Veeam Backup & Replication',
  backupexec:    'Veritas Backup Exec',
  netbackup:     'Veritas NetBackup',
  vinchin:       'Vinchin Backup & Recovery',
  kiberbackup:   'Кибербекап (Киберпротект)',
}

export default function Import() {
  const { t } = useI18n()
  const [format, setFormat] = useState<Format>('veeam')
  const [files, setFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [warnings, setWarnings] = useState<string[]>([])
  const [sets, setSets] = useState<ImportedSet[]>([])

  const [locations, setLocations] = useState<Location[]>([])
  const [locationId, setLocationId] = useState<number | ''>('')
  const [onDuplicate, setOnDuplicate] = useState<'create_new' | 'merge_by_tapes'>('create_new')

  const [result, setResult] = useState<ImportResult | null>(null)

  useEffect(() => { getLocations().then(setLocations) }, [])

  const hasPreview = sets.length > 0
  const totalTapes = sets.reduce((s, set) => s + set.tapes.length, 0)

  const handleUpload = async () => {
    if (!files.length) return
    setLoading(true)
    setError('')
    setSets([])
    setWarnings([])
    setResult(null)
    try {
      const results = await Promise.all(
        files.map(async f => ({
          preview: await importPreview(format, f),
          stem: f.name.replace(/\.[^.]+$/, ''),
        }))
      )
      const allSets = results.flatMap(({ preview, stem }) =>
        preview.sets.map(s => {
          const name = s.name || stem
          return { ...s, name, recording_date: s.recording_date ?? guessDateFromText(name) }
        })
      )
      const allWarnings = results.flatMap(r => r.preview.warnings)
      setSets(allSets.map(s => ({ ...s, description: null, retention_days: 365, retention_forever: false })))
      setWarnings(allWarnings)
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t('import.parse_error'))
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async () => {
    if (!sets.length) return
    setLoading(true)
    setError('')
    try {
      const res = await importExecute(sets, locationId !== '' ? locationId : null, onDuplicate)
      setResult(res)
      setSets([])
      setWarnings([])
      setFiles([])
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t('import.import_error'))
    } finally {
      setLoading(false)
    }
  }

  const setField = (i: number, field: keyof ImportedSet, value: unknown) =>
    setSets(prev => prev.map((s, idx) => idx === i ? { ...s, [field]: value } : s))

  const removeTape = (setIdx: number, tapeIdx: number) =>
    setSets(prev =>
      prev.map((s, i) => i !== setIdx ? s : { ...s, tapes: s.tapes.filter((_, j) => j !== tapeIdx) })
          .filter(s => s.tapes.length > 0)
    )

  const setTapeLto = (setIdx: number, tapeIdx: number, lto: string) =>
    setSets(prev => prev.map((s, i) => i !== setIdx ? s : {
      ...s, tapes: s.tapes.map((tp, j) => j !== tapeIdx ? tp : { ...tp, lto_version: lto || null }),
    }))

  const removeSet = (i: number) => setSets(prev => prev.filter((_, idx) => idx !== i))

  return (
    <div>
      <h1 className={styles.title}>{t('import.title')}</h1>

      {/* Upload form */}
      <div className={shared.card}>
        <div className={styles.uploadRow}>
          <select
            className={styles.formatSelect}
            value={format}
            onChange={e => setFormat(e.target.value as Format)}
          >
            {(Object.keys(FORMAT_LABELS) as Format[]).map(f => (
              <option key={f} value={f}>{FORMAT_LABELS[f]}</option>
            ))}
          </select>
          <input
            ref={fileInputRef}
            className={styles.fileInput}
            type="file"
            accept=".csv,.xlsx,.xls"
            multiple
            onChange={e => setFiles(e.target.files ? Array.from(e.target.files) : [])}
          />
        </div>
        {files.length > 1 && (
          <p className={styles.filesNote}>
            {t('import.files_selected', { n: files.length, names: files.map(f => f.name).join(', ') })}
          </p>
        )}
        <div className={styles.uploadActions}>
          <button className={shared.btnPrimary} onClick={handleUpload} disabled={!files.length || loading}>
            {loading && !hasPreview ? t('import.parsing') : t('import.upload')}
          </button>
        </div>
        {error && <p className={styles.uploadError}>{error}</p>}
      </div>

      {/* Preview */}
      {hasPreview && (
        <>
          <div className={styles.previewHeader}>
            <h2 className={styles.previewTitle}>
              {t('import.preview_title')} — {sets.length} {t('import.sets_word')}, {totalTapes} {t('import.tapes_word')}
            </h2>
          </div>

          {warnings.length > 0 && (
            <div className={styles.warningsBox}>
              {warnings.map((w, i) => <p key={i} className={styles.warningItem}>⚠ {w}</p>)}
            </div>
          )}

          <div className={styles.setList}>
            {sets.map((s, i) => (
              <div key={i} className={shared.card}>
                <div className={styles.setCardHeader}>
                  <span className={styles.setCardIndex}>{t('import.set_n', { n: i + 1, total: sets.length })}</span>
                  <button onClick={() => removeSet(i)} className={styles.btnRemoveSet}>
                    {t('import.remove_set')}
                  </button>
                </div>

                <div className={styles.setFieldRow}>
                  <Field label={t('import.set_name')}>
                    <input className={shared.input} value={s.name} onChange={e => setField(i, 'name', e.target.value)} />
                  </Field>
                </div>
                <div className={styles.setFieldRow}>
                  <Field label={t('common.description')}>
                    <textarea className={styles.textarea} value={s.description ?? ''} onChange={e => setField(i, 'description', e.target.value || null)} />
                  </Field>
                </div>
                <div className={styles.dateGrid}>
                  <Field label={t('import.recording_date')}>
                    <DateInput className={shared.input} value={s.recording_date ?? ''} onChange={v => setField(i, 'recording_date', v || null)} />
                  </Field>
                  <Field label={t('import.sent_date')}>
                    <DateInput className={shared.input} value={s.sent_date ?? ''} onChange={v => setField(i, 'sent_date', v || null)} />
                  </Field>
                </div>
                <div className={styles.setFieldRow}>
                  <Field label={t('import.retention_days')}>
                    <div className={styles.retentionRow}>
                      <input
                        type="number"
                        min={1}
                        className={styles.retentionInput}
                        value={s.retention_days ?? ''}
                        disabled={s.retention_forever}
                        onChange={e => setField(i, 'retention_days', e.target.value ? Number(e.target.value) : null)}
                      />
                      <label className={styles.retentionForeverLabel}>
                        <input
                          type="checkbox"
                          checked={s.retention_forever}
                          onChange={e => setField(i, 'retention_forever', e.target.checked)}
                        />
                        {t('import.retention_forever')}
                      </label>
                    </div>
                  </Field>
                </div>
                <div className={styles.setFieldRow}>
                  <Field label={t('common.notes')}>
                    <textarea className={styles.textarea} value={s.notes ?? ''} onChange={e => setField(i, 'notes', e.target.value || null)} />
                  </Field>
                </div>

                <div className={styles.tapesSection}>
                  <div className={styles.tapesSectionTitle}>{t('import.tapes_section')} ({s.tapes.length})</div>
                  <div className={styles.tapesGrid}>
                    {s.tapes.map((tp, j) => (
                      <div key={j} className={styles.tapeItem}>
                        <span className={styles.tapeLabel}>{tp.label}</span>
                        <select
                          className={styles.tapeLtoSelect}
                          value={tp.lto_version ?? ''}
                          onChange={e => setTapeLto(i, j, e.target.value)}
                        >
                          <option value="">— LTO —</option>
                          {LTO_OPTIONS.map(v => <option key={v} value={v}>{v}</option>)}
                        </select>
                        <button onClick={() => removeTape(i, j)} className={styles.btnRemoveTape}>✕</button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Import params */}
          <div className={styles.paramsCard}>
            <h3 className={styles.paramsTitle}>{t('import.params_title')}</h3>
            <div className={styles.paramsFields}>
              <Field label={t('import.location')}>
                <select className={styles.locationSelect} value={locationId} onChange={e => setLocationId(e.target.value === '' ? '' : Number(e.target.value))}>
                  <option value="">{t('import.location_none')}</option>
                  {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
              </Field>
              <Field label={t('import.on_duplicate')}>
                <div className={styles.radioGroup}>
                  {([
                    ['create_new',     t('import.dup_create_new')],
                    ['merge_by_tapes', t('import.dup_merge')],
                  ] as const).map(([val, label]) => (
                    <label key={val} className={styles.radioLabel}>
                      <input type="radio" value={val} checked={onDuplicate === val} onChange={() => setOnDuplicate(val)} />
                      {label}
                    </label>
                  ))}
                </div>
              </Field>
            </div>
            <div className={styles.importActions}>
              <button className={shared.btnPrimary} onClick={handleImport} disabled={loading}>
                {loading ? t('import.importing') : t('import.do_import', { n: sets.length })}
              </button>
              <button className={shared.btnSecondary} onClick={() => { setSets([]); setWarnings([]) }}>{t('common.cancel')}</button>
            </div>
          </div>
        </>
      )}

      {result && (
        <div className={styles.resultCard}>
          <h3 className={styles.resultTitle}>{t('import.done_title')}</h3>
          <div className={styles.resultStats}>
            <ResultStat label={t('import.created_sets')} value={result.created_sets} />
            <ResultStat label={t('import.created_tapes')} value={result.created_tapes} />
            {result.updated_sets > 0 && <ResultStat label={t('import.updated_sets')} value={result.updated_sets} />}
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className={styles.fieldLabel}>{label}</label>
      {children}
    </div>
  )
}

function ResultStat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className={styles.resultStatValue}>{value}</div>
      <div className={styles.resultStatLabel}>{label}</div>
    </div>
  )
}
