import { useEffect, useState, useCallback, Fragment } from 'react'
import { getUsers, createUser, updateUser, deleteUser } from '../api'
import type { User, UserRole } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import shared from '../styles/shared.module.css'
import styles from './Users.module.css'

export default function Users() {
  const [users, setUsers] = useState<User[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState({ username: '', password: '', role: 'readonly' as UserRole, language: 'ru' })
  const [editForm, setEditForm] = useState({ password: '', role: 'user' as UserRole, is_active: true, language: 'ru' })
  const [error, setError] = useState('')
  const { user: me } = useAuth()
  const { t } = useI18n()

  const load = useCallback(() => getUsers().then(setUsers), [])
  useEffect(() => { load() }, [load])

  const handleCreate = async () => {
    setError('')
    if (!form.username || !form.password) { setError(t('users.fill_required')); return }
    try {
      await createUser(form)
      setShowForm(false)
      setForm({ username: '', password: '', role: 'user', language: 'ru' })
      load()
    } catch (e: any) {
      setError(e.response?.data?.detail ?? t('common.error'))
    }
  }

  const openEdit = (u: User) => {
    setEditingId(u.id)
    setEditForm({ password: '', role: u.role, is_active: u.is_active, language: u.language ?? 'ru' })
  }

  const handleUpdate = async () => {
    if (!editingId) return
    const payload: { password?: string; role: UserRole; is_active: boolean; language: string } = {
      role: editForm.role,
      is_active: editForm.is_active,
      language: editForm.language,
    }
    if (editForm.password) payload.password = editForm.password
    await updateUser(editingId, payload)
    setEditingId(null)
    load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('users.delete_confirm'))) return
    await deleteUser(id)
    load()
  }

  return (
    <div>
      <div className={shared.pageHeader}>
        <h1>{t('users.title')}</h1>
        <button className={shared.btnPrimary} onClick={() => setShowForm(true)}>{t('common.add')}</button>
      </div>

      {showForm && (
        <div className={shared.formCard}>
          <h3 className={styles.formCardTitle}>{t('users.new')}</h3>
          <div className={shared.formGrid}>
            <Field label={t('users.username')}><input className={shared.input} value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} /></Field>
            <Field label={t('users.password')}><input className={shared.input} type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} /></Field>
            <Field label={t('users.role')}>
              <select className={shared.input} value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value as UserRole }))}>
                <option value="readonly">{t('users.role_readonly')}</option>
                <option value="user">{t('users.role_user')}</option>
                <option value="admin">{t('users.role_admin')}</option>
              </select>
            </Field>
            <Field label={t('users.language')}>
              <select className={shared.input} value={form.language} onChange={e => setForm(f => ({ ...f, language: e.target.value }))}>
                <option value="ru">{t('users.lang_ru')}</option>
                <option value="en">{t('users.lang_en')}</option>
              </select>
            </Field>
          </div>
          {error && <p className={styles.formCardError}>{error}</p>}
          <div className={styles.formCardActions}>
            <button className={shared.btnPrimary} onClick={handleCreate}>{t('users.create')}</button>
            <button className={shared.btnSecondary} onClick={() => { setShowForm(false); setError('') }}>{t('common.cancel')}</button>
          </div>
        </div>
      )}

      <table className={styles.table}>
        <thead>
          <tr className={styles.tableHead}>
            <th className={shared.th}>{t('users.username')}</th>
            <th className={shared.th}>{t('users.role')}</th>
            <th className={shared.th}>{t('users.language')}</th>
            <th className={shared.th}>{t('users.status')}</th>
            <th className={shared.th}></th>
          </tr>
        </thead>
        <tbody>
          {users.map(u => (
            <Fragment key={u.id}>
              <tr className={editingId === u.id ? styles.tableRowEditing : styles.tableRow}>
                <td className={shared.td}>
                  <b>{u.username}</b>
                  {u.id === me?.id && <span className={styles.meLabel}>{t('users.me')}</span>}
                </td>
                <td className={shared.td}>
                  <span className={u.role === 'admin' ? styles.roleBadgeAdmin : u.role === 'readonly' ? styles.roleBadgeReadonly : styles.roleBadgeUser}>
                    {u.role === 'admin' ? t('users.role_admin') : u.role === 'readonly' ? t('users.role_readonly') : t('users.role_user')}
                  </span>
                </td>
                <td className={shared.td}>
                  <span className={styles.langLabel}>
                    {(u.language ?? 'ru') === 'en' ? t('users.lang_en') : t('users.lang_ru')}
                  </span>
                </td>
                <td className={shared.td}>
                  <span className={u.is_active ? styles.statusActive : styles.statusInactive}>
                    {u.is_active ? t('users.active') : t('users.inactive')}
                  </span>
                </td>
                <td className={shared.td}>
                  <button className={shared.btnSm} onClick={() => editingId === u.id ? setEditingId(null) : openEdit(u)}>
                    {editingId === u.id ? t('common.cancel') : t('common.edit')}
                  </button>
                  {u.id !== me?.id && (
                    <button className={styles.btnSmDelete} onClick={() => handleDelete(u.id)}>{t('common.delete')}</button>
                  )}
                </td>
              </tr>
              {editingId === u.id && (
                <tr className={styles.editRow}>
                  <td colSpan={5} className={styles.editCell}>
                    <div className={styles.editRowInner}>
                      <Field label={t('users.new_password')}>
                        <input className={styles.inputPassword} type="password" value={editForm.password} onChange={e => setEditForm(f => ({ ...f, password: e.target.value }))} />
                      </Field>
                      <Field label={t('users.role')}>
                        <select className={styles.inputRole} value={editForm.role} onChange={e => setEditForm(f => ({ ...f, role: e.target.value as UserRole }))}>
                          <option value="readonly">{t('users.role_readonly')}</option>
                          <option value="user">{t('users.role_user')}</option>
                          <option value="admin">{t('users.role_admin')}</option>
                        </select>
                      </Field>
                      <Field label={t('users.language')}>
                        <select className={styles.inputLang} value={editForm.language} onChange={e => setEditForm(f => ({ ...f, language: e.target.value }))}>
                          <option value="ru">{t('users.lang_ru')}</option>
                          <option value="en">{t('users.lang_en')}</option>
                        </select>
                      </Field>
                      <Field label={t('users.status')}>
                        <select className={styles.inputLang} value={editForm.is_active ? '1' : '0'} onChange={e => setEditForm(f => ({ ...f, is_active: e.target.value === '1' }))}>
                          <option value="1">{t('users.active')}</option>
                          <option value="0">{t('users.inactive')}</option>
                        </select>
                      </Field>
                      <button className={styles.btnSaveInline} onClick={handleUpdate}>{t('common.save')}</button>
                    </div>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
          {users.length === 0 && (
            <tr><td colSpan={5} className={styles.noData}>{t('common.no_data')}</td></tr>
          )}
        </tbody>
      </table>
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
