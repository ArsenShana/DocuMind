import { Link, NavLink } from 'react-router-dom'
import { FileSearch } from 'lucide-react'

export default function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="navbar-logo">
        <div className="logo-icon"><FileSearch size={18} color="white" /></div>
        DocuMind
      </Link>
      <div className="navbar-links">
        <NavLink to="/" end>Home</NavLink>
        <NavLink to="/dashboard">Dashboard</NavLink>
        <a href="/api/docs" target="_blank" rel="noreferrer">API Docs</a>
      </div>
      <div className="navbar-actions">
        <Link to="/dashboard" className="btn btn-primary btn-sm">Launch App</Link>
      </div>
    </nav>
  )
}
