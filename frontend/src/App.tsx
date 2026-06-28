import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { I18nProvider, useI18n } from './i18n/I18nContext'
import Dashboard from './pages/Dashboard'
import Sets from './pages/Sets'
import SetDetail from './pages/SetDetail'
import Locations from './pages/Locations'
import Users from './pages/Users'
import Login from './pages/Login'
import Import from './pages/Import'
import Search from './pages/Search'
import Log from './pages/Log'
import styles from './App.module.css'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <I18nProvider>
          <Routes>
            <Route path="/login" element={<LoginRoute />} />
            <Route path="/*" element={<ProtectedLayout />} />
          </Routes>
        </I18nProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

function LoginRoute() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/" replace />
  return <Login />
}

function ProtectedLayout() {
  const { user, loading, signOut } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()

  if (loading) return null
  if (!user) return <Navigate to="/login" replace />

  const handleLogout = () => { signOut(); navigate('/login') }

  return (
    <div className={styles.layout}>
      <nav className={styles.sidebar}>
        <div className={styles.sidebarLogo}>
          <img src="/favicon.svg" alt="" className={styles.sidebarLogoImg} />
          <span className={styles.sidebarTitle}>TapeRotation</span>
        </div>

        <NavLink to="/" end className={({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`}>{t('nav.dashboard')}</NavLink>
        <NavLink to="/sets" className={({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`}>{t('nav.sets')}</NavLink>
        <NavLink to="/search" className={({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`}>{t('nav.search')}</NavLink>
        <NavLink to="/locations" className={({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`}>{t('nav.locations')}</NavLink>
        {user.role !== 'readonly' && (
          <NavLink to="/import" className={({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`}>{t('nav.import')}</NavLink>
        )}
        {user.role === 'admin' && (
          <NavLink to="/users" className={({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`}>{t('nav.users')}</NavLink>
        )}
        {user.role === 'admin' && (
          <NavLink to="/log" className={({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`}>{t('nav.log')}</NavLink>
        )}

        <div className={styles.sidebarFooter}>
          <div className={styles.sidebarUser}>
            {user.username}
            {user.role === 'admin' && (
              <span className={styles.sidebarUserAdmin}>(admin)</span>
            )}
          </div>
          <button onClick={handleLogout} className={styles.logoutBtn}>{t('nav.logout')}</button>
        </div>
      </nav>

      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sets" element={<Sets />} />
          <Route path="/sets/:id" element={<SetDetail />} />
          <Route path="/locations" element={<Locations />} />
          <Route path="/search" element={<Search />} />
          {user.role !== 'readonly' && <Route path="/import" element={<Import />} />}
          {user.role === 'admin' && <Route path="/users" element={<Users />} />}
          {user.role === 'admin' && <Route path="/log" element={<Log />} />}
        </Routes>
      </main>
    </div>
  )
}
