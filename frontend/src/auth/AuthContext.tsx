import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import type { User } from '../api/types'
import { getMe } from '../api'

interface AuthContextValue {
  user: User | null
  token: string | null
  signIn: (token: string) => Promise<void>
  signOut: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextValue>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) { setLoading(false); return }
    getMe()
      .then(setUser)
      .catch(() => { localStorage.removeItem('token'); setToken(null) })
      .finally(() => setLoading(false))
  }, [token])

  const signIn = async (newToken: string) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
    const me = await getMe()
    setUser(me)
  }

  const signOut = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, signIn, signOut, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
