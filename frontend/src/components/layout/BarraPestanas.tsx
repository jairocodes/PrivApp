import { Link, useLocation } from 'react-router-dom'
import { SECCIONES, esSeccionActual } from '@/components/layout/secciones'

/** Pestañas inferiores del celular: siempre visibles y con texto en cada icono. */
export default function BarraPestanas() {
  const { pathname } = useLocation()

  return (
    <nav
      aria-label="Navegación principal"
      className="fixed inset-x-0 bottom-0 z-30 border-t border-borde bg-superficie pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      <ul className="grid grid-cols-5">
        {SECCIONES.map((seccion) => {
          const activa = esSeccionActual(seccion, pathname)
          const Icono = seccion.icono
          return (
            <li key={seccion.ruta}>
              <Link
                to={seccion.ruta}
                aria-current={activa ? 'page' : undefined}
                className={`flex min-h-[60px] flex-col items-center justify-center gap-1 text-xs ${
                  activa ? 'font-bold text-marca-texto' : 'font-medium text-texto-2'
                }`}
              >
                <span
                  className={`flex h-8 w-14 items-center justify-center rounded-full ${activa ? 'bg-marca-suave' : ''}`}
                >
                  <Icono size={22} aria-hidden="true" />
                </span>
                {seccion.etiqueta}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
