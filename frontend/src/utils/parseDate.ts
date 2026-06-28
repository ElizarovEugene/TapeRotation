import dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'

dayjs.extend(customParseFormat)

const FORMATS = [
  'YYYY-MM-DD', 'YYYY/MM/DD',
  'DD.MM.YYYY', 'D.M.YYYY',
  'DD/MM/YYYY', 'D/M/YYYY',
  'DD-MM-YYYY', 'D-M-YYYY',
  'MM/DD/YYYY',
]

export function parsePastedDate(text: string): string | null {
  const s = text.trim()
  if (!s) return null
  for (const fmt of FORMATS) {
    const d = dayjs(s, fmt, true)
    if (d.isValid()) return d.format('YYYY-MM-DD')
  }
  return null
}

const NAME_DATE_PATTERNS = [
  /(?<!\d)(\d{4})[-_.](\d{2})[-_.](\d{2})(?!\d)/,  // 2026-06-19 / 2026_06_19 / 2026.06.19
  /(?<!\d)(\d{2})[-_.](\d{2})[-_.](\d{4})(?!\d)/,  // 19-06-2026 / 19.06.2026
  /(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)/,            // 20260619
]

export function guessDateFromText(text: string): string | null {
  if (!text) return null
  for (const pat of NAME_DATE_PATTERNS) {
    const m = pat.exec(text)
    if (!m) continue
    const [, g1, g2, g3] = m
    const [year, month, day] = g1.length === 4 ? [g1, g2, g3] : [g3, g2, g1]
    if (Number(year) < 1990 || Number(year) > 2099) continue
    const d = dayjs(`${year}-${month}-${day}`, 'YYYY-MM-DD', true)
    if (d.isValid()) return d.format('YYYY-MM-DD')
  }
  return null
}
