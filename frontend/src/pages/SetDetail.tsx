import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getSet, createTape, updateTape, deleteTape, markReturned, getSetHistory } from '../api'
import type { TapeSet, Tape, AuditLog } from '../api/types'
import StatusBadge from '../components/StatusBadge'
import { useI18n } from '../i18n/I18nContext'
import dayjs from 'dayjs'
import { useAuth } from '../auth/AuthContext'
import shared from '../styles/shared.module.css'
import styles from './SetDetail.module.css'
import { LTO_OPTIONS } from '../constants'
import { formatAuditDetails } from '../utils/auditDetails'

interface EditState {
  label: string
  lto_version: string
  status: 'written' | 'blank'
}

export default function SetDetail() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const { t } = useI18n()
  const canWrite = user?.role !== 'readonly'
  const [set, setSet] = useState<TapeSet | null>(null)
  const [newLabel, setNewLabel] = useState('')
  const [newLto, setNewLto] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editState, setEditState] = useState<EditState>({ label: '', lto_version: '', status: 'written' })
  const [history, setHistory] = useState<AuditLog[]>([])
  const [showHistory, setShowHistory] = useState(false)

  const load = () => getSet(Number(id)).then(setSet)
  const loadHistory = () => getSetHistory(Number(id)).then(setHistory)

  useEffect(() => { load() }, [id])

  const startEdit = (tp: Tape) => {
    setEditingId(tp.id)
    setEditState({ label: tp.label, lto_version: tp.lto_version ?? '', status: tp.status })
  }

  const cancelEdit = () => setEditingId(null)

  const saveEdit = async () => {
    if (!editingId) return
    await updateTape(editingId, {
      label: editState.label.trim() || editState.label,
      set_id: Number(id),
      status: editState.status,
      lto_version: editState.lto_version || null,
      notes: null,
    })
    setEditingId(null)
    load()
  }

  const handleAddTape = async () => {
    if (!newLabel.trim()) return
    await createTape({ label: newLabel.trim(), set_id: Number(id), status: 'written', lto_version: newLto || null, notes: null })
    setNewLabel('')
    setNewLto('')
    load()
  }

  const handleDeleteTape = async (tid: number) => {
    if (!confirm(t('set_detail.delete_tape_confirm'))) return
    await deleteTape(tid)
    load()
  }

  const handleReturn = async () => {
    if (!set || !confirm(t('set_detail.return_confirm'))) return
    await markReturned(set.id)
    load()
  }

  const handlePrint = () => {
    if (!set) return
    const loc = set.location
    const status = t(`status.${set.status}` as any)
    const recordingDate = set.recording_date ? dayjs(set.recording_date).format('DD.MM.YYYY') : null
    const sentDate = set.sent_date ? dayjs(set.sent_date).format('DD.MM.YYYY') : '—'
    const retention = set.retention_forever
      ? t('set_detail.retention_forever')
      : `${set.retention_days} ${t('set_detail.retention_days_unit')}`
    const expires = set.retention_forever
      ? t('set_detail.retention_forever')
      : set.expires_at ? dayjs(set.expires_at).format('DD.MM.YYYY') : '—'
    const contact = loc?.contact_name
      ? `${loc.contact_name}${loc.contact_phone ? ' · ' + loc.contact_phone : ''}`
      : null
    const tapeRows = set.tapes.map((tp, i) => `
      <tr>
        <td>${i + 1}</td>
        <td><code>${tp.label}</code></td>
        <td>${tp.lto_version ?? '—'}</td>
        <td>${tp.status === 'written' ? t('tape_status.written') : t('tape_status.blank')}</td>
      </tr>`).join('')
    const notesBlock = set.notes
      ? `<div class="notes"><b>${t('set_detail.notes_label')}</b><p>${set.notes.replace(/</g, '&lt;')}</p></div>`
      : ''
    const html = `<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>TapeRotation — ${set.name}</title>
<style>
  body { font-family: Arial, sans-serif; margin: 24px; font-size: 13px; color: #111; }
  h1 { font-size: 20px; margin-bottom: 4px; }
  .subtitle { color: #555; margin-bottom: 20px; font-size: 13px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
  .card { border: 1px solid #ccc; border-radius: 6px; padding: 12px 16px; }
  .card h3 { font-size: 11px; color: #888; margin: 0 0 10px; text-transform: uppercase; letter-spacing: 0.05em; }
  .row { display: flex; gap: 8px; margin-bottom: 6px; font-size: 13px; }
  .lbl { color: #888; min-width: 130px; flex-shrink: 0; }
  .notes { margin-bottom: 20px; }
  .notes b { font-size: 13px; }
  .notes p { white-space: pre-wrap; margin: 6px 0; color: #444; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
  th, td { padding: 7px 10px; border: 1px solid #ddd; text-align: left; }
  thead tr { background: #f5f5f5; }
  code { font-family: monospace; }
  .footer { margin-top: 28px; font-size: 11px; color: #aaa; border-top: 1px solid #eee; padding-top: 8px; }
  @media print { @page { margin: 1.5cm; } }
</style>
</head>
<body>
<h1>TapeRotation — ${set.name}</h1>
<div class="subtitle">${status}${set.description ? ' · ' + set.description : ''}</div>
<div class="grid">
  <div class="card">
    <h3>${t('common.location')}</h3>
    <div class="row"><span class="lbl">${t('set_detail.location')}</span><span>${loc?.name ?? '—'}</span></div>
    ${loc?.address ? `<div class="row"><span class="lbl">${t('set_detail.address')}</span><span>${loc.address}</span></div>` : ''}
    ${contact ? `<div class="row"><span class="lbl">${t('set_detail.contact')}</span><span>${contact}</span></div>` : ''}
  </div>
  <div class="card">
    <h3>${t('set_detail.sent_date')}</h3>
    ${recordingDate ? `<div class="row"><span class="lbl">${t('set_detail.recording_date')}</span><span style="font-weight:600;color:#1a5fa8">${recordingDate}</span></div>` : ''}
    <div class="row"><span class="lbl">${t('set_detail.added_at')}</span><span>${dayjs(set.created_at).format('DD.MM.YYYY HH:mm')}</span></div>
    <div class="row"><span class="lbl">${t('set_detail.sent_date')}</span><span>${sentDate}</span></div>
    <div class="row"><span class="lbl">${t('set_detail.retention')}</span><span>${retention}</span></div>
    <div class="row"><span class="lbl">${t('set_detail.expires')}</span><span>${expires}</span></div>
  </div>
</div>
${notesBlock}
<h2 style="font-size:14px;margin-bottom:8px;">${t('set_detail.tapes_in_set')} (${set.tapes.length})</h2>
<table>
  <thead><tr><th>#</th><th>${t('set_detail.tape_label')}</th><th>${t('set_detail.lto_version')}</th><th>${t('common.status')}</th></tr></thead>
  <tbody>${tapeRows}</tbody>
</table>
<div class="footer">${t('set_detail.printed_on')}: ${dayjs().format('DD.MM.YYYY HH:mm')}</div>
<script>window.print(); window.close();</script>
</body>
</html>`
    const win = window.open('', '_blank')
    if (win) { win.document.write(html); win.document.close() }
  }

  const handleToggleHistory = () => {
    if (!showHistory) loadHistory()
    setShowHistory(v => !v)
  }

  if (!set) return <p>{t('common.loading')}</p>

  return (
    <div>
      <div className={styles.backRow}>
        <Link to="/sets" className={styles.backLink}>{t('set_detail.back')}</Link>
      </div>

      <div className={styles.headerRow}>
        <div className={styles.headerLeft}>
          <h1 className={styles.titleRow}>{set.name}</h1>
          {set.description && <p className={styles.description}>{set.description}</p>}
        </div>
        <div className={styles.headerRight}>
          <button onClick={handlePrint} className={shared.btnSecondary}>
            {t('set_detail.print')}
          </button>
          <StatusBadge status={set.status} />
        </div>
      </div>

      <div className={styles.infoGrid}>
        <InfoCard>
          <InfoRow label={t('set_detail.location')} value={set.location?.name ?? '—'} />
          {set.location?.address && <InfoRow label={t('set_detail.address')} value={set.location.address} />}
          {set.location?.contact_name && <InfoRow label={t('set_detail.contact')} value={`${set.location.contact_name}${set.location.contact_phone ? ' · ' + set.location.contact_phone : ''}`} />}
        </InfoCard>
        <InfoCard>
          {set.recording_date && (
            <InfoRow label={t('set_detail.recording_date')} value={dayjs(set.recording_date).format('DD.MM.YYYY')} highlight />
          )}
          <InfoRow label={t('set_detail.added_at')} value={dayjs(set.created_at).format('DD.MM.YYYY HH:mm')} />
          <InfoRow label={t('set_detail.sent_date')} value={set.sent_date ? dayjs(set.sent_date).format('DD.MM.YYYY') : '—'} />
          <InfoRow
            label={t('set_detail.retention')}
            value={set.retention_forever ? t('set_detail.retention_forever') : `${set.retention_days} ${t('set_detail.retention_days_unit')}`}
          />
          <InfoRow
            label={t('set_detail.expires')}
            value={set.retention_forever ? t('set_detail.retention_forever') : set.expires_at ? dayjs(set.expires_at).format('DD.MM.YYYY') : '—'}
          />
        </InfoCard>
      </div>

      {set.notes && (
        <div className={styles.notes}>
          <b>{t('set_detail.notes_label')}</b>
          <p className={styles.notesPre}>{set.notes}</p>
        </div>
      )}

      {/* Tapes */}
      <section>
        <h2 className={styles.tapesHeading}>{t('set_detail.tapes_in_set')} ({set.tapes.length})</h2>
        {canWrite && (
          <div className={styles.addTapeRow}>
            <input
              className={styles.inputSm}
              placeholder={t('set_detail.tape_placeholder')}
              value={newLabel}
              onChange={e => setNewLabel(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAddTape()}
            />
            <select className={styles.inputSmLto} value={newLto} onChange={e => setNewLto(e.target.value)}>
              <option value="">— LTO —</option>
              {LTO_OPTIONS.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
            <button onClick={handleAddTape} className={shared.btnPrimary}>{t('set_detail.add_tape')}</button>
          </div>
        )}
        {set.tapes.length === 0 ? (
          <p className={styles.noTapes}>{t('set_detail.no_tapes')}</p>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr className={styles.tableHead}>
                <th className={shared.th}>{t('set_detail.tape_label')}</th>
                <th className={shared.th}>{t('set_detail.lto_version')}</th>
                <th className={shared.th}>{t('common.status')}</th>
                {canWrite && <th className={styles.thActions}></th>}
              </tr>
            </thead>
            <tbody>
              {set.tapes.map((tp: Tape) => (
                <tr key={tp.id} className={styles.tableRow}>
                  {editingId === tp.id ? (
                    <>
                      <td className={shared.td}>
                        <input
                          className={styles.inputSmFull}
                          value={editState.label}
                          onChange={e => setEditState(s => ({ ...s, label: e.target.value }))}
                        />
                      </td>
                      <td className={shared.td}>
                        <select
                          className={styles.inputSmLto}
                          value={editState.lto_version}
                          onChange={e => setEditState(s => ({ ...s, lto_version: e.target.value }))}
                        >
                          <option value="">—</option>
                          {LTO_OPTIONS.map(v => <option key={v} value={v}>{v}</option>)}
                        </select>
                      </td>
                      <td className={shared.td}>
                        <select
                          className={styles.inputSmStatus}
                          value={editState.status}
                          onChange={e => setEditState(s => ({ ...s, status: e.target.value as 'written' | 'blank' }))}
                        >
                          <option value="written">{t('tape_status.written')}</option>
                          <option value="blank">{t('tape_status.blank')}</option>
                        </select>
                      </td>
                      <td className={shared.td}>
                        <button onClick={saveEdit} className={styles.btnSmSave}>{t('common.save')}</button>
                        <button onClick={cancelEdit} className={styles.btnSmCancel}>{t('common.cancel')}</button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className={shared.td}>{tp.label}</td>
                      <td className={tp.lto_version ? styles.tdLtoBlue : styles.tdLtoMuted}>{tp.lto_version ?? '—'}</td>
                      <td className={shared.td}>{tp.status === 'written' ? t('tape_status.written') : t('tape_status.blank')}</td>
                      {canWrite && (
                        <td className={shared.td}>
                          <button onClick={() => startEdit(tp)} className={shared.btnSm}>{t('common.edit')}</button>
                          <button onClick={() => handleDeleteTape(tp.id)} className={styles.btnSmDelete}>{t('common.delete')}</button>
                        </td>
                      )}
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Actions */}
      {canWrite && set.status !== 'returned' && (
        <div className={styles.returnSection}>
          <button onClick={handleReturn} className={styles.btnReturn}>
            {t('set_detail.mark_returned')}
          </button>
        </div>
      )}

      {/* History */}
      <section className={styles.historySection}>
        <button onClick={handleToggleHistory} className={shared.btnSecondary}>
          {showHistory ? t('set_detail.hide_history') : t('set_detail.show_history')}
        </button>
        {showHistory && (
          <div className={styles.historyContent}>
            {history.length === 0 ? (
              <p className={styles.noHistory}>{t('set_detail.no_history')}</p>
            ) : (
              <table className={styles.historyTable}>
                <thead>
                  <tr className={styles.tableHead}>
                    <th className={shared.th}>{t('set_detail.history_date')}</th>
                    <th className={shared.th}>{t('set_detail.history_action')}</th>
                    <th className={shared.th}>{t('set_detail.history_user')}</th>
                    <th className={shared.th}>{t('set_detail.history_details')}</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(h => {
                    const details = formatAuditDetails(h.details, t)
                    const isKeyEvent = h.action === 'set_created' || h.action === 'set_moved' || h.action === 'recording_date_set' || h.action === 'set_returned'
                    return (
                      <tr key={h.id} className={isKeyEvent ? styles.tableRowKey : styles.tableRow}>
                        <td className={styles.tdNoWrap}>
                          {dayjs(h.created_at).format('DD.MM.YYYY HH:mm')}
                        </td>
                        <td className={isKeyEvent ? styles.tdKeyAction : shared.td}>
                          {t(`action.${h.action}` as any) ?? h.action}
                        </td>
                        <td className={shared.td}>{h.actor ?? '—'}</td>
                        <td className={styles.tdMuted}>{details}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

function InfoCard({ children }: { children: React.ReactNode }) {
  return (
    <div className={styles.infoCard}>
      {children}
    </div>
  )
}

function InfoRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={styles.infoRow}>
      <span className={styles.infoLabel}>{label}</span>
      <span className={highlight ? styles.infoValueHighlight : undefined}>{value}</span>
    </div>
  )
}
