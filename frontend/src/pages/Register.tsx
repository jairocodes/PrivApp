import Bienvenida from '@/components/auth/Bienvenida'
import RegisterForm from '@/components/auth/RegisterForm'

export default function Register() {
  return (
    <main className="flex flex-col items-center px-4 py-6">
      <div className="w-full max-w-md">
        <Bienvenida titulo="Crear cuenta" subtitulo="Regístrate gratis para analizar políticas y guardar tus resultados." />
        <RegisterForm />
      </div>
    </main>
  )
}
