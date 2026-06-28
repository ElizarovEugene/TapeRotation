import { parsePastedDate } from '../utils/parseDate'

interface Props {
  className?: string
  value: string
  onChange: (value: string) => void
}

export default function DateInput({ className, value, onChange }: Props) {
  return (
    <input
      type="date"
      className={className}
      value={value}
      onChange={e => onChange(e.target.value)}
      onPaste={e => {
        const parsed = parsePastedDate(e.clipboardData.getData('text'))
        if (parsed) {
          e.preventDefault()
          onChange(parsed)
        }
      }}
    />
  )
}
