import { NavLink } from 'react-router-dom'
import { useThemeStore } from '../../store/themeStore'

export function Navbar() {
  const { theme, toggle } = useThemeStore()

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1 rounded text-sm font-medium transition-colors ${
      isActive
        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800'
    }`

  return (
    <nav className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex h-14 items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-bold text-gray-900 dark:text-white text-sm tracking-widest mr-4">
            CRIP
          </span>
          <NavLink to="/" className={linkClass} end>Dashboard</NavLink>
          <NavLink to="/analyst" className={linkClass}>Analyst</NavLink>
          <NavLink to="/personas" className={linkClass}>Personas</NavLink>
        </div>
        <button
          onClick={toggle}
          aria-label="Toggle theme"
          className="p-1.5 rounded text-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
      </div>
    </nav>
  )
}
