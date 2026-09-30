import { Link } from 'react-router-dom'
import { Users } from 'lucide-react'
import Navbar from '@/components/common/Navbar'

export default function Admin() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
        <h1 className="text-xl font-bold text-gray-900 mb-2">Administración</h1>
        <p className="text-sm text-gray-500 mb-6">
          Desde aquí se accede a la gestión de usuarios y del corpus normativo.
        </p>

        <Link
          to="/admin/usuarios"
          className="card flex items-center gap-3 hover:border-blue-300 hover:shadow-md transition-all"
        >
          <Users size={22} className="text-blue-600 shrink-0" aria-hidden="true" />
          <div>
            <p className="font-semibold text-gray-900">Usuarios</p>
            <p className="text-sm text-gray-500">Consultar las cuentas y activarlas o desactivarlas.</p>
          </div>
        </Link>
      </main>
    </div>
  )
}
