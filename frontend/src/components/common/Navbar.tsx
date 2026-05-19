import { Link } from 'react-router-dom'
import { ShieldCheck, LogOut } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

export default function Navbar() {
  const { user, logout } = useAuth()

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-2 text-blue-600 font-semibold text-lg">
          <ShieldCheck size={22} />
          PrivApp
        </Link>

        {user && (
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600 hidden sm:block">{user.nombre}</span>
            <button
              onClick={logout}
              aria-label="Cerrar sesión"
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-600 transition-colors"
            >
              <LogOut size={16} />
              <span className="hidden sm:block">Salir</span>
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
