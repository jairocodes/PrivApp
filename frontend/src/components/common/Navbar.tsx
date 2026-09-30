import { Link } from 'react-router-dom'
import { LogOut, Settings, ShieldCheck, UserRound } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { esAdministrador } from '@/types/auth'

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
            {esAdministrador(user) && (
              <Link
                to="/admin"
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-blue-600 transition-colors"
              >
                <Settings size={16} aria-hidden="true" />
                <span>Administración</span>
              </Link>
            )}
            <Link
              to="/perfil"
              aria-label="Mi perfil"
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-blue-600 transition-colors"
            >
              <UserRound size={16} aria-hidden="true" />
              <span className="hidden sm:block">{user.nombre}</span>
            </Link>
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
