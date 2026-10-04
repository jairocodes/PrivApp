import { ShieldCheck } from 'lucide-react'
import RegisterForm from '@/components/auth/RegisterForm'

export default function Register() {
  return (
    <main className="flex flex-col items-center justify-center px-4 py-8">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-2 mb-8">
          <ShieldCheck size={40} className="text-marca-texto" />
          <h1 className="text-2xl font-bold text-texto">Crear cuenta</h1>
          <p className="text-sm text-texto-2 text-center">
            Regístrate para comenzar a analizar políticas
          </p>
        </div>
        <RegisterForm />
      </div>
    </main>
  )
}
