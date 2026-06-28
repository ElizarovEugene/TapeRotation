import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import styles from './Login.module.css'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signIn } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) return
    setLoading(true)
    setError('')
    try {
      const { access_token } = await login(username, password)
      await signIn(access_token)
      navigate('/')
    } catch {
      setError(t('login.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.bg}>
      <form onSubmit={handleSubmit} className={styles.card}>
        <div className={styles.logoRow}>
          <img src="/favicon.svg" alt="" className={styles.logoImg} />
          <h1 className={styles.logoTitle}>TapeRotation</h1>
        </div>

        <div className={styles.fieldWrapper}>
          <label className={styles.label}>{t('login.username')}</label>
          <input
            className={styles.input}
            autoFocus
            autoComplete="username"
            value={username}
            onChange={e => setUsername(e.target.value)}
          />
        </div>
        <div className={styles.fieldWrapperLast}>
          <label className={styles.label}>{t('login.password')}</label>
          <input
            className={styles.input}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </div>

        {error && <p className={styles.error}>{error}</p>}

        <button type="submit" disabled={loading} className={styles.btn}>
          {loading ? t('login.signing_in') : t('login.submit')}
        </button>
      </form>
    </div>
  )
}
