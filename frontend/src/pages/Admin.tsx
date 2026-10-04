import { Link } from 'react-router-dom'
import { Library, Users } from 'lucide-react'

export default function Admin() {
  return (
    <>

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
        <h1 className="text-xl font-bold text-texto mb-2">Administración</h1>
        <p className="text-sm text-texto-2 mb-6">
          Desde aquí se accede a la gestión de usuarios y del corpus normativo.
        </p>

        <Link
          to="/admin/usuarios"
          className="card flex items-center gap-3 hover:border-marca-borde hover:shadow-md transition-all"
        >
          <Users size={22} className="text-marca-texto shrink-0" aria-hidden="true" />
          <div>
            <p className="font-semibold text-texto">Usuarios</p>
            <p className="text-sm text-texto-2">Consultar las cuentas y activarlas o desactivarlas.</p>
          </div>
        </Link>

        <Link
          to="/admin/corpus"
          className="card flex items-center gap-3 mt-3 hover:border-marca-borde hover:shadow-md transition-all"
        >
          <Library size={22} className="text-marca-texto shrink-0" aria-hidden="true" />
          <div>
            <p className="font-semibold text-texto">Corpus normativo</p>
            <p className="text-sm text-texto-2">Consultar, cargar y activar o desactivar documentos normativos.</p>
          </div>
        </Link>
      </main>
    </>
  )
}
