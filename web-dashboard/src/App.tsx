import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import AdminPanel from './pages/AdminPanel'
import './App.css'

function Sidebar() {
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname.startsWith('/dashboard')
    return location.pathname === path
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
            to="/admin"
            className={isActive('/admin') ? 'active' : ''}
            onClick={() => setMobileOpen(false)}
          >
            <span className="sidebar-nav-icon">⚙️</span>
            Admin Panel
          </Link>
        </nav>

        <div className="sidebar-footer">
          <span className="status-dot" />
          System Online
        </div>
      </aside>
    </>
  )
}

function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard/farm-001" replace />} />
            <Route path="/dashboard/:farmId" element={<Dashboard />} />
            <Route path="/admin" element={<AdminPanel />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
