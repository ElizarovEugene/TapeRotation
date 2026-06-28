import { useState } from 'react'
import type { TapeSet, Location } from '../api/types'
import { createSet, updateSet, createTape } from '../api'
import { useI18n } from '../i18n/I18nContext'
import shared from '../styles/shared.module.css'
import styles from './SetModal.module.css'
import { LTO_OPTIONS } from '../constants'
import DateInput from '../components/DateInput'

interface TapeRow {
  label: string
  lto_version: string
}

interface Props {
  set: TapeSet | null
  locations: Location[]
  existingNames?: string[]
  onClose: () => void
  onSaved: () => void
}

export default function SetModal({ set, locations, existingNames = [], onClose, onSaved }: Props) {
  const { t } = useI18n()
  const [form, setForm] = useState({
    name: set?.name ?? '',
    description: set?.description ?? '',
    location_id: set?.location_id ?? '',
    recording_date: set?.recording_date ?? '',
    sent_date: set?.sent_date ?? '',
    retention_days: set?.retention_days ?? 365,
    retention_forever: set?.retention_forever ?? false,
    notes: set?.notes ?? '',
  })
  const [tapes, setTapes] = useState<TapeRow[]>(
    set
      ? set.tapes.map(tp => ({ label: tp.label, lto_version: tp.lto_version ?? '' }))
      : [{ label: '', lto_version: '' }]
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const update = (k: string, v: unknown) => setForm(f => ({ ...f, [k]: v }))

  const updateTape = (i: number, field: keyof TapeRow, val: string) =>
    setTapes(rows => rows.map((r, idx) => idx === i ? { ...r, [field]: val } : r))

  const addTapeRow = () => setTapes(r => [...r, { label: '', lto_version: '' }])

  const removeTapeRow = (i: number) =>
    setTapes(r => r.length === 1 ? [{ label: '', lto_version: '' }] : r.filter((_, idx) => idx !== i))

  const handleKeyDown = (e: React.KeyboardEvent, i: number) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (i === tapes.length - 1) addTapeRow()
    }
  }

  const handleSave = async () => {
    if (!form.name.trim()) { setError(t('set_modal.name_required')); return }
    setSaving(true)
    try {
      const payload = {
        ...form,
        location_id: form.location_id ? Number(form.location_id) : null,
        recording_date: form.recording_date || null,
        sent_date: form.sent_date || null,
        description: form.description || null,
        notes: form.notes || null,
        retention_days: Number(form.retention_days),
      }

      if (set) {
        await updateSet(set.id, payload)
      } else {
        const created = await createSet(payload)
        const filledTapes = tapes.filter(tp => tp.label.trim())
        await Promise.all(
          filledTapes.map(tp =>
            createTape({
              label: tp.label.trim(),
              set_id: created.id,
              status: 'written',
              lto_version: tp.lto_version || null,
              notes: null,
            })
          )
        )
      }
      onSaved()
    } catch {
      setError(t('set_modal.save_error'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <h2 className={styles.title}>{set ? t('set_modal.edit') : t('set_modal.new')}</h2>

        <Field label={t('set_modal.name_label')}>
          <input
            className={shared.input}
            list="set-names-list"
            value={form.name}
            onChange={e => update('name', e.target.value)}
          />
          <datalist id="set-names-list">
            {existingNames.map(n => <option key={n} value={n} />)}
          </datalist>
        </Field>
        <Field label={t('common.description')}>
          <textarea className={styles.textarea} value={form.description} onChange={e => update('description', e.target.value)} />
        </Field>
        <Field label={t('common.location')}>
          <select className={shared.input} value={form.location_id} onChange={e => update('location_id', e.target.value)}>
            <option value="">{t('set_modal.location_none')}</option>
            {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </Field>
        <div className={styles.formGrid}>
          <Field label={t('set_modal.recording_date')}>
            <DateInput className={shared.input} value={form.recording_date} onChange={v => update('recording_date', v)} />
          </Field>
          <Field label={t('set_modal.sent_date')}>
            <DateInput className={shared.input} value={form.sent_date} onChange={v => update('sent_date', v)} />
          </Field>
        </div>
        <Field label={t('set_modal.retention_days')}>
          <div className={styles.retentionRow}>
            <input
              className={styles.inputFlex}
              type="number"
              min={1}
              value={form.retention_days}
              disabled={form.retention_forever}
              onChange={e => update('retention_days', e.target.value)}
            />
            <label className={styles.retentionForeverLabel}>
              <input
                type="checkbox"
                checked={form.retention_forever}
                onChange={e => update('retention_forever', e.target.checked)}
              />
              {t('set_modal.retention_forever')}
            </label>
          </div>
        </Field>
        <Field label={t('common.notes')}>
          <textarea className={styles.textarea} value={form.notes} onChange={e => update('notes', e.target.value)} />
        </Field>

        {!set && (
          <Field label={t('set_modal.tapes_label')}>
            <div className={styles.tapesList}>
              {tapes.map((tp, i) => (
                <div key={i} className={styles.tapeRow}>
                  <input
                    className={styles.tapeInput}
                    placeholder={t('set_modal.tape_placeholder', { n: i + 1 })}
                    value={tp.label}
                    onChange={e => updateTape(i, 'label', e.target.value)}
                    onKeyDown={e => handleKeyDown(e, i)}
                    autoFocus={i === tapes.length - 1 && i > 0}
                  />
                  <select
                    className={styles.tapeLtoSelect}
                    value={tp.lto_version}
                    onChange={e => updateTape(i, 'lto_version', e.target.value)}
                    title="LTO"
                  >
                    <option value="">— LTO —</option>
                    {LTO_OPTIONS.filter(Boolean).map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                  <button
                    type="button"
                    onClick={() => removeTapeRow(i)}
                    className={styles.btnRemove}
                    title={t('common.delete')}
                  >✕</button>
                </div>
              ))}
              <button type="button" onClick={addTapeRow} className={styles.btnAdd}>
                {t('set_modal.add_tape')}
              </button>
            </div>
          </Field>
        )}

        {error && <p className={styles.error}>{error}</p>}

        <div className={styles.footer}>
          <button className={shared.btnSecondary} onClick={onClose}>{t('common.cancel')}</button>
          <button className={shared.btnPrimary} onClick={handleSave} disabled={saving}>
            {saving ? t('common.saving') : t('common.save')}
          </button>
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className={styles.fieldWrapper}>
      <label className={styles.fieldLabel}>{label}</label>
      {children}
    </div>
  )
}
