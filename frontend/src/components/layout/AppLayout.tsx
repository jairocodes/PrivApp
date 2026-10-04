import { Outlet } from 'react-router-dom'
import Footer from '@/components/common/Footer'
import Navbar from '@/components/common/Navbar'
import BarraPestanas from '@/components/layout/BarraPestanas'
import { useAuth } from '@/hooks/useAuth'

/** Estructura de las pantallas con barra superior: con sesión, además, las
 *  pestañas inferiores en el celular. Cada página aporta su propio <main>. */
export default function AppLayout() {
  const { user } = useAuth()

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-marca focus:px-4 focus:py-3 focus:font-semibold focus:text-white"
      >
        Saltar al contenido
      </a>
      <Navbar />
      <div id="contenido" tabIndex={-1} className="flex-1 outline-none">
        <Outlet />
      </div>
      <Footer />
      {user && (
        <>
          {/* Reserva el alto de las pestañas para que no tapen el pie de página. */}
          <div aria-hidden="true" className="h-20 md:hidden" />
          <BarraPestanas />
        </>
      )}
    </div>
  )
}
