import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import AdminPanel from './pages/AdminPanel'
import FarmerDashboard from './pages/FarmerDashboard'
import './App.css'

function Sidebar() {
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const { logout, user } = useAuth()

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname.startsWith('/dashboard')
    if (path === '/farmer-dashboard') return location.pathname === '/farmer-dashboard'
    return location.pathname === path
  }

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  return (
    <>
      <button
        className="mobile-toggle"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Toggle navigation"
      >
        {mobileOpen ? '✕' : '☰'}
      </button>

      <div
        className={`mobile-overlay ${mobileOpen ? 'open' : ''}`}
        onClick={() => setMobileOpen(false)}
      />

      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <h1>
            <span className="sidebar-brand-icon">🌱</span>
            CarbonReady
          </h1>
          <p>Carbon Intelligence Platform</p>
        </div>

        <nav className="sidebar-nav">
          <Link
            to="/dashboard/farm-001"
            className={isActive('/dashboard') ? 'active' : ''}
            onClick={() => setMobileOpen(false)}
          >
            <span className="sidebar-nav-icon">📊</span>
            Dashboard
          </Link>
          <Link
            to="/farmer-dashboard"
            className={isActive('/farmer-dashboard') ? 'active' : ''}
            onClick={() => setMobileOpen(false)}
          >
            <span className="sidebar-nav-icon">🌾</span>
            Farmer View
          </Link>
          <Link
            to="/admin"
            className={isActive('/admin') ? 'active' : ''}
            onClick={() => setMobileOpen(false)}
          >
            <span className="sidebar-nav-icon">⚙️</span>
            Admin Panel
          </Link>
        </nav>

        <div className="sidebar-footer">
          <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: '#a0a0a0' }}>
            {user?.username || 'User'}
          </div>
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              padding: '0.5rem',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '0.9rem',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.15)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.1)'
            }}
          >
            Sign Out
          </button>
          <div style={{ marginTop: '0.75rem' }}>
            <span className="status-dot" />
            System Online
          </div>
        </div>
      </aside>
    </>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #1a4d2e 0%, #2d5a3d 100%)',
        color: 'white'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🌱</div>
          <div>Loading...</div>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AppContent() {
  const location = useLocation()
  const isLoginPage = location.pathname === '/login'

  if (isLoginPage) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
      </Routes>
    )
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard/farm-001" replace />} />
          <Route
            path="/dashboard/:farmId"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/farmer-dashboard"
            element={
              <ProtectedRoute>
                <FarmerDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminPanel />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AppContent />
      </Router>
    </AuthProvider>
  )
}

export default App
