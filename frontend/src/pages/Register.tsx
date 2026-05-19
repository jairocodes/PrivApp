import { ShieldCheck } from 'lucide-react'
import RegisterForm from '@/components/auth/RegisterForm'

export default function Register() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-2 mb-8">
          <ShieldCheck size={40} className="text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Crear cuenta</h1>
          <p className="text-sm text-gray-500 text-center">
            Regístrate para comenzar a analizar políticas
          </p>
        </div>
        <RegisterForm />
      </div>
    </main>
  )
}
