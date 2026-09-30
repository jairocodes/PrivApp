import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import Navbar from '@/components/common/Navbar'
import { useUsuariosAdmin } from '@/hooks/useUsuariosAdmin'
import type { UsuarioAdmin } from '@/types/admin'

export default function AdminUsuarios() {
  const { items, total, page, pageSize, isLoading, error, cargar } = useUsuariosAdmin()
  const [texto, setTexto] = useState('')

  useEffect(() => {
    cargar(1, '')
  }, [])

  const totalPaginas = Math.max(1, Math.ceil(total / pageSize))

  const buscar = (e: React.FormEvent) => {
    e.preventDefault()
    cargar(1, texto.trim())
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-3xl mx-auto px-4 py-6 pb-16">
        <div className="flex items-center gap-3 mb-6">
          <Link
            to="/admin"
            className="p-2 rounded-lg hover:bg-gray-200 text-gray-500 transition-colors"
            aria-label="Volver a administración"
          >
            <ArrowLeft size={20} />
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Usuarios</h1>
        </div>

        <form onSubmit={buscar} role="search" className="flex gap-2 mb-5">
          <label htmlFor="busqueda-usuarios" className="sr-only">
            Buscar por nombre o correo
          </label>
          <input
            id="busqueda-usuarios"
            type="search"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Buscar por nombre o correo"
            className="input-field flex-1"
          />
          <button type="submit" className="btn-primary inline-flex items-center gap-1 text-sm">
            <Search size={16} aria-hidden="true" />
            Buscar
          </button>
        </form>

        {isLoading && <p className="text-sm text-gray-500 text-center py-10">Cargando usuarios...</p>}
        {error && !isLoading && (
          <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
            {error}
          </p>
        )}
        {!isLoading && !error && items.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-10">No se encontraron usuarios.</p>
        )}

        {!isLoading && !error && items.length > 0 && (
          <>
            <ul className="space-y-3">
              {items.map((usuario) => (
                <FilaUsuario key={usuario.id} usuario={usuario} />
              ))}
            </ul>

            <div className="flex items-center justify-between mt-5">
              <button
                onClick={() => cargar(page - 1)}
                disabled={page <= 1}
                className="flex items-center gap-1 text-sm text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:text-blue-600"
              >
                <ChevronLeft size={16} />
                Anterior
              </button>
              <span className="text-xs text-gray-400">
                Página {page} de {totalPaginas}
              </span>
              <button
                onClick={() => cargar(page + 1)}
                disabled={page >= totalPaginas}
                className="flex items-center gap-1 text-sm text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:text-blue-600"
              >
                Siguiente
                <ChevronRight size={16} />
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

function FilaUsuario({ usuario }: { usuario: UsuarioAdmin }) {
  const fecha = new Date(usuario.created_at).toLocaleDateString('es-GT', {
    day: '2-digit', month: 'short', year: 'numeric',
  })

  return (
    <li className="card flex items-center justify-between gap-3">
      <div className="min-w-0">
        <p className="font-medium text-gray-900 truncate">{usuario.nombre}</p>
        <p className="text-sm text-gray-500 truncate">{usuario.email}</p>
        <p className="text-xs text-gray-400 mt-1">
          {usuario.role === 'administrador' ? 'Administrador' : 'Usuario'} · Registrado el {fecha}
        </p>
      </div>
      <span
        className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-semibold ${
          usuario.is_active ? 'bg-riesgo-bajo/15 text-riesgo-bajo' : 'bg-gray-100 text-gray-600'
        }`}
      >
        {usuario.is_active ? 'Activa' : 'Desactivada'}
      </span>
    </li>
  )
}
