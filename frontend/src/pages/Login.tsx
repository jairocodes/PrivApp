import { useLocation } from 'react-router-dom'
import Bienvenida from '@/components/auth/Bienvenida'
import LoginForm from '@/components/auth/LoginForm'
import Aviso from '@/components/common/Aviso'

export default function Login() {
  // Por ejemplo, la confirmación de que la cuenta se eliminó.
  const mensaje = (useLocation().state as { mensaje?: string } | null)?.mensaje

  return (
    <main className="flex flex-col items-center px-4 py-6">
      <div className="w-full max-w-md">
        <Bienvenida titulo="PrivApp" subtitulo="Entiende en minutos qué hace cada app con tus datos personales." />
        {mensaje && <Aviso tipo="exito" className="mb-4">{mensaje}</Aviso>}
        <LoginForm />
      </div>
    </main>
  )
}
