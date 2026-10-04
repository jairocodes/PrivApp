import { Link, useLocation } from 'react-router-dom'
import { BookOpen, LogOut, Settings, ShieldCheck, UserRound } from 'lucide-react'
import BotonTema from '@/components/common/BotonTema'
import { SECCIONES, esSeccionActual } from '@/components/layout/secciones'
import { useAuth } from '@/hooks/useAuth'
import { esAdministrador } from '@/types/auth'

const ENLACE = 'inline-flex min-h-[44px] items-center gap-2 rounded-xl px-3 text-sm font-semibold transition-colors'
const ENLACE_ACTIVO = 'bg-marca-suave text-marca-suave-texto'
const ENLACE_INACTIVO = 'text-texto-2 hover:bg-superficie-2 hover:text-texto'

// En el celular, Glosario y Perfil están en las pestañas inferiores (BarraPestanas);
// aquí se muestran desde md, o siempre si no hay sesión.
const SECCIONES_SUPERIORES = SECCIONES.filter((s) => ['/dashboard', '/analizar', '/historial'].includes(s.ruta))

export default function Navbar() {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()
  const glosarioActivo = pathname === '/glosario'

  return (
    <header className="sticky top-0 z-30 border-b border-borde bg-superficie">
      <div className="mx-auto flex h-16 max-w-5xl items-center gap-2 px-4">
        <Link to="/dashboard" className="mr-2 flex items-center gap-2 text-lg font-extrabold text-marca-texto">
          <ShieldCheck size={24} aria-hidden="true" />
          PrivApp
        </Link>

        {user && (
          <nav aria-label="Secciones" className="hidden items-center gap-1 md:flex">
            {SECCIONES_SUPERIORES.map((seccion) => {
              const activa = esSeccionActual(seccion, pathname)
              return (
                <Link
                  key={seccion.ruta}
                  to={seccion.ruta}
                  aria-current={activa ? 'page' : undefined}
                  className={`${ENLACE} ${activa ? ENLACE_ACTIVO : ENLACE_INACTIVO}`}
                >
                  {seccion.etiqueta}
                </Link>
              )
            })}
          </nav>
        )}

        <div className="ml-auto flex items-center gap-1">
          <Link
            to="/glosario"
            aria-label="Glosario"
            aria-current={glosarioActivo ? 'page' : undefined}
            className={`${ENLACE} ${glosarioActivo ? ENLACE_ACTIVO : ENLACE_INACTIVO} ${user ? 'hidden md:inline-flex' : ''}`}
          >
            <BookOpen size={18} aria-hidden="true" />
            <span className="hidden sm:inline">Glosario</span>
          </Link>
          {user && esAdministrador(user) && (
            <Link to="/admin" className={`${ENLACE} ${pathname.startsWith('/admin') ? ENLACE_ACTIVO : ENLACE_INACTIVO}`}>
              <Settings size={18} aria-hidden="true" />
              <span>Administración</span>
            </Link>
          )}
          {user && (
            <Link
              to="/perfil"
              aria-label="Mi perfil"
              aria-current={pathname === '/perfil' ? 'page' : undefined}
              className={`${ENLACE} ${pathname === '/perfil' ? ENLACE_ACTIVO : ENLACE_INACTIVO} hidden md:inline-flex`}
            >
              <UserRound size={18} aria-hidden="true" />
              <span>{user.nombre}</span>
            </Link>
          )}
          <BotonTema />
          {user && (
            <button
              type="button"
              onClick={logout}
              aria-label="Cerrar sesión"
              className={`${ENLACE} text-texto-2 hover:bg-riesgo-alto/10 hover:text-riesgo-alto`}
            >
              <LogOut size={18} aria-hidden="true" />
              <span className="hidden lg:inline">Salir</span>
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
