import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { esAdministrador } from '@/types/auth'

// Solo oculta la navegación: el servidor verifica el rol en cada ruta administrativa.
export default function AdminRoute() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Cargando...</p>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />
  return esAdministrador(user) ? <Outlet /> : <Navigate to="/dashboard" replace />
}
