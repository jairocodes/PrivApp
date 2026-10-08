import { Link } from 'react-router-dom'
import { ArrowRight, Library, Users } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import EncabezadoPagina from '@/components/common/EncabezadoPagina'

const OPCIONES: { ruta: string; titulo: string; descripcion: string; icono: LucideIcon }[] = [
  {
    ruta: '/admin/usuarios',
    titulo: 'Usuarios',
    descripcion: 'Consultar las cuentas y activarlas o desactivarlas.',
    icono: Users,
  },
  {
    ruta: '/admin/corpus',
    titulo: 'Corpus normativo',
    descripcion: 'Consultar, cargar y activar o desactivar documentos normativos.',
    icono: Library,
  },
]

export default function Admin() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-6 pb-16">
      <EncabezadoPagina
        titulo="Administración"
        subtitulo="Desde aquí se accede a la gestión de usuarios y del corpus normativo."
      />

      <div className="grid gap-3 sm:grid-cols-2">
        {OPCIONES.map(({ ruta, titulo, descripcion, icono: Icono }) => (
          <Link
            key={ruta}
            to={ruta}
            className="flex items-center gap-4 rounded-2xl border border-borde bg-superficie p-5 transition-colors hover:border-marca-borde"
          >
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-marca-suave text-marca-texto">
              <Icono size={24} aria-hidden="true" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block font-bold text-texto">{titulo}</span>
              <span className="block text-sm text-texto-2">{descripcion}</span>
            </span>
            <ArrowRight size={20} aria-hidden="true" className="shrink-0 text-texto-3" />
          </Link>
        ))}
      </div>
    </main>
  )
}
