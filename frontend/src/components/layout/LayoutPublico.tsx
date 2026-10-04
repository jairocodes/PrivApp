import { Outlet } from 'react-router-dom'
import BotonTema from '@/components/common/BotonTema'
import Footer from '@/components/common/Footer'

/** Inicio de sesión y registro: sin barra de navegación, con el interruptor del tema. */
export default function LayoutPublico() {
  return (
    <div className="flex min-h-screen flex-col">
      <div className="flex justify-end px-4 pt-4">
        <BotonTema />
      </div>
      <div className="flex-1">
        <Outlet />
      </div>
      <Footer />
    </div>
  )
}
