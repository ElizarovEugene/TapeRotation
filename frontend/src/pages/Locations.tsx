import { useEffect, useState, useCallback } from 'react'
import { getLocations, createLocation, updateLocation, deleteLocation } from '../api'
import type { Location } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import shared from '../styles/shared.module.css'
import styles from './Locations.module.css'

export default function Locations() {
  const { user } = useAuth()
  const { t } = useI18n()
  const canWrite = user?.role !== 'readonly'
  const [locations, setLocations] = useState<Location[]>([])
  const [editing, setEditing] = useState<Location | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm())

  const load = useCallback(() => getLocations().then(setLocations), [])
  useEffect(() => { load() }, [load])

  const openNew = () => { setEditing(null); setForm(emptyForm()); setShowForm(true) }
  const openEdit = (l: Location) => { setEditing(l); setForm({ name: l.name, address: l.address ?? '', contact_name: l.contact_name ?? '', contact_phone: l.contact_phone ?? '', notes: l.notes ?? '' }); setShowForm(true) }

  const handleSave = async () => {
    if (!form.name.trim()) return
    const payload = {
      name: form.name,
      address: form.address || null,
      contact_name: form.contact_name || null,
      contact_phone: form.contact_phone || null,
      notes: form.notes || null,
    }
    if (editing) {
      await updateLocation(editing.id, payload)
    } else {
      await createLocation(payload)
    }
    setShowForm(false)
    load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('locations.delete_confirm'))) return
    await deleteLocation(id)
    load()
  }

  return (
    <div>
      <div className={shared.pageHeader}>
        <h1>{t('locations.title')}</h1>
        {canWrite && <button className={shared.btnPrimary} onClick={openNew}>{t('common.add')}</button>}
      </div>

      {showForm && (
        <div className={styles.formSection}>
          <h3 className={styles.formSectionTitle}>{editing ? t('locations.edit') : t('locations.new')}</h3>
          <div className={shared.formGrid}>
            <Field label={t('locations.name')}><input className={shared.input} value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></Field>
            <Field label={t('locations.address')}><input className={shared.input} value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))} /></Field>
            <Field label={t('locations.contact')}><input className={shared.input} value={form.contact_name} onChange={e => setForm(f => ({ ...f, contact_name: e.target.value }))} /></Field>
            <Field label={t('locations.phone')}><input className={shared.input} value={form.contact_phone} onChange={e => setForm(f => ({ ...f, contact_phone: e.target.value }))} /></Field>
          </div>
          <Field label={t('locations.notes')}><textarea className={styles.textarea} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></Field>
          <div className={styles.formActions}>
            <button className={shared.btnPrimary} onClick={handleSave}>{t('common.save')}</button>
            <button className={shared.btnSecondary} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
          </div>
        </div>
      )}

      <table className={styles.table}>
        <thead>
          <tr className={styles.tableHead}>
            <th className={shared.th}>{t('common.name')}</th>
            <th className={shared.th}>{t('locations.address')}</th>
            <th className={shared.th}>{t('locations.contact')}</th>
            <th className={shared.th}>{t('locations.phone')}</th>
            <th className={shared.th}></th>
          </tr>
        </thead>
        <tbody>
          {locations.map(l => (
            <tr key={l.id} className={styles.tableRow}>
              <td className={shared.td}><b>{l.name}</b></td>
              <td className={shared.td}>{l.address ?? '—'}</td>
              <td className={shared.td}>{l.contact_name ?? '—'}</td>
              <td className={shared.td}>{l.contact_phone ?? '—'}</td>
              <td className={shared.td}>
                {canWrite && <>
                  <button className={shared.btnSm} onClick={() => openEdit(l)}>{t('common.edit')}</button>
                  <button className={styles.btnSmDelete} onClick={() => handleDelete(l.id)}>{t('common.delete')}</button>
                </>}
              </td>
            </tr>
          ))}
          {locations.length === 0 && (
            <tr><td colSpan={5} className={styles.noData}>{t('common.no_data')}</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

function emptyForm() {
  return { name: '', address: '', contact_name: '', contact_phone: '', notes: '' }
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className={styles.fieldWrapper}>
      <label className={styles.fieldLabel}>{label}</label>
      {children}
    </div>
  )
}
