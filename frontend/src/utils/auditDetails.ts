import dayjs from 'dayjs'

type T = (key: any, vars?: Record<string, string | number>) => string

export function formatAuditDetails(details: string | null, t: T): string {
  try {
    const d = JSON.parse(details ?? '{}')
    return Object.entries(d).map(([k, v]) => {
      const label = t(`detail.${k}` as any) ?? k
      let val: unknown = v
      if (v === null || v === undefined) {
        val = '-'
      } else if (k === 'format') {
        val = t(v === 'merge_by_tapes' ? 'import.dup_merge' : 'import.dup_create_new')
      } else if (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v)) {
        val = dayjs(v).format('DD.MM.YYYY')
      } else if (Array.isArray(v)) {
        val = v.length ? v.map(item => typeof item === 'string' ? t(`field.${item}` as any) : item).join(', ') : '-'
      }
      return `${label}: ${val}`
    }).join(', ')
  } catch {
    return details ?? ''
  }
}
