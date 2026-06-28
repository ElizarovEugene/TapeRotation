export type UserRole = 'readonly' | 'user' | 'admin'

export interface User {
  id: number
  username: string
  role: UserRole
  is_active: boolean
  language: string
  created_at: string
}

export type SetStatus = 'in_storage' | 'expired' | 'returned'
export type TapeStatus = 'blank' | 'written'

export interface Location {
  id: number
  name: string
  address: string | null
  contact_name: string | null
  contact_phone: string | null
  notes: string | null
}

export interface Tape {
  id: number
  label: string
  set_id: number | null
  status: TapeStatus
  lto_version: string | null
  notes: string | null
}

export interface TapeSet {
  id: number
  name: string
  description: string | null
  location_id: number | null
  location: Location | null
  sent_date: string | null
  recording_date: string | null
  retention_days: number
  retention_forever: boolean
  expires_at: string | null
  status: SetStatus
  notes: string | null
  created_at: string
  tapes: Tape[]
}

export interface Stats {
  total_sets: number
  in_storage: number
  expired: number
  returned: number
  expiring_soon: number
}

export interface ImportedTape {
  label: string
  status: string
  lto_version: string | null
}

export interface ImportedSet {
  name: string
  tapes: ImportedTape[]
  description: string | null
  sent_date: string | null
  recording_date: string | null
  retention_days: number | null
  retention_forever: boolean
  expires_at: string | null
  notes: string | null
}

export interface ImportPreview {
  sets: ImportedSet[]
  warnings: string[]
}

export interface ImportResult {
  created_sets: number
  created_tapes: number
  updated_sets: number
}

export interface AuditLog {
  id: number
  set_id: number | null
  action: string
  actor: string | null
  details: string | null
  created_at: string
}

export interface AuditLogFull extends AuditLog {
  set_name: string | null
}

export interface TapeSearchResult {
  tape_id: number
  tape_label: string
  tape_lto_version: string | null
  tape_status: TapeStatus
  set_id: number | null
  set_name: string | null
  set_status: SetStatus | null
  recording_date: string | null
  expires_at: string | null
}
