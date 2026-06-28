import api from './client'
import type { Location, TapeSet, Tape, Stats, SetStatus, User, ImportPreview, ImportResult, ImportedSet, AuditLog, AuditLogFull, TapeSearchResult } from './types'

// Auth
export const login = (username: string, password: string) =>
  api.post<{ access_token: string }>('/auth/login', { username, password }).then(r => r.data)
export const getMe = () => api.get<User>('/auth/me').then(r => r.data)

// Users (admin)
export const getUsers = () => api.get<User[]>('/users/').then(r => r.data)
export const createUser = (data: { username: string; password: string; role: string; language?: string }) =>
  api.post<User>('/users/', data).then(r => r.data)
export const updateUser = (id: number, data: { password?: string; role?: string; is_active?: boolean; language?: string }) =>
  api.put<User>(`/users/${id}`, data).then(r => r.data)
export const deleteUser = (id: number) => api.delete(`/users/${id}`)

// Locations
export const getLocations = () => api.get<Location[]>('/locations/').then(r => r.data)
export const createLocation = (data: Omit<Location, 'id'>) => api.post<Location>('/locations/', data).then(r => r.data)
export const updateLocation = (id: number, data: Omit<Location, 'id'>) => api.put<Location>(`/locations/${id}`, data).then(r => r.data)
export const deleteLocation = (id: number) => api.delete(`/locations/${id}`)

// TapeSets
export const getSets = (params?: { status?: SetStatus; location_id?: number }) =>
  api.get<TapeSet[]>('/sets/', { params }).then(r => r.data)
export const getSet = (id: number) => api.get<TapeSet>(`/sets/${id}`).then(r => r.data)
export const getExpiredSets = () => api.get<TapeSet[]>('/sets/expired').then(r => r.data)
export const getExpiringSets = (days?: number) =>
  api.get<TapeSet[]>('/sets/expiring', { params: { days } }).then(r => r.data)
export const getStats = () => api.get<Stats>('/sets/stats').then(r => r.data)
export const createSet = (data: Partial<TapeSet>) => api.post<TapeSet>('/sets/', data).then(r => r.data)
export const updateSet = (id: number, data: Partial<TapeSet>) => api.put<TapeSet>(`/sets/${id}`, data).then(r => r.data)
export const markReturned = (id: number) => api.patch<TapeSet>(`/sets/${id}/return`).then(r => r.data)
export const deleteSet = (id: number) => api.delete(`/sets/${id}`)

// Import
export const importPreview = (format: string, file: File): Promise<ImportPreview> => {
  const fd = new FormData()
  fd.append('format', format)
  fd.append('file', file)
  return api.post<ImportPreview>('/import/preview', fd).then(r => r.data)
}
export const importExecute = (sets: ImportedSet[], location_id: number | null, on_duplicate: string): Promise<ImportResult> =>
  api.post<ImportResult>('/import/execute', { sets, location_id, on_duplicate }).then(r => r.data)

// History
export const getSetHistory = (id: number) =>
  api.get<AuditLog[]>(`/sets/${id}/history`).then(r => r.data)

// Admin log (full audit trail)
export const getAuditLog = () =>
  api.get<AuditLogFull[]>('/admin/log').then(r => r.data)

// Search
export const searchTapes = (q: string) =>
  api.get<TapeSearchResult[]>('/search/', { params: { q } }).then(r => r.data)

// Tapes
export const getTapes = (set_id?: number) =>
  api.get<Tape[]>('/tapes/', { params: set_id !== undefined ? { set_id } : {} }).then(r => r.data)
export const createTape = (data: Omit<Tape, 'id'>) => api.post<Tape>('/tapes/', data).then(r => r.data)
export const updateTape = (id: number, data: Omit<Tape, 'id'>) => api.put<Tape>(`/tapes/${id}`, data).then(r => r.data)
export const deleteTape = (id: number) => api.delete(`/tapes/${id}`)
