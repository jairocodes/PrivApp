import { ShieldCheck } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import LoginForm from '@/components/auth/LoginForm'

export default function Login() {
  // Por ejemplo, la confirmación de que la cuenta se eliminó.
  const mensaje = (useLocation().state as { mensaje?: string } | null)?.mensaje

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-2 mb-8">
          <ShieldCheck size={40} className="text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">PrivApp</h1>
          <p className="text-sm text-gray-500 text-center">
            Análisis de políticas de privacidad
          </p>
        </div>
        {mensaje && (
          <p role="status" className="mb-4 text-sm text-riesgo-bajo bg-riesgo-bajo/10 rounded-lg px-3 py-2">
            {mensaje}
          </p>
        )}
        <LoginForm />
      </div>
    </main>
  )
}
