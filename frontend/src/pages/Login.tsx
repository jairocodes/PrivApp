import { ShieldCheck } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import LoginForm from '@/components/auth/LoginForm'
import Aviso from '@/components/common/Aviso'

export default function Login() {
  // Por ejemplo, la confirmación de que la cuenta se eliminó.
  const mensaje = (useLocation().state as { mensaje?: string } | null)?.mensaje

  return (
    <main className="flex flex-col items-center justify-center px-4 py-8">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-2 mb-8">
          <ShieldCheck size={40} className="text-marca-texto" />
          <h1 className="text-2xl font-bold text-texto">PrivApp</h1>
          <p className="text-sm text-texto-2 text-center">
            Análisis de políticas de privacidad
          </p>
        </div>
        {mensaje && (
          <Aviso tipo="exito" className="mb-4">{mensaje}</Aviso>
        )}
        <LoginForm />
      </div>
    </main>
  )
}
