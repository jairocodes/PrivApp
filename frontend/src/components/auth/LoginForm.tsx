import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import Button from '@/components/common/Button'
import Input from '@/components/common/Input'

interface FormState {
  email: string
  password: string
}

interface FormErrors {
  email?: string
  password?: string
  general?: string
}

export default function LoginForm() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState<FormState>({ email: '', password: '' })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)

  const validate = (): boolean => {
    const newErrors: FormErrors = {}
    if (!form.email) newErrors.email = 'El correo es obligatorio.'
    if (!form.password) newErrors.password = 'La contraseña es obligatoria.'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    setIsLoading(true)
    setErrors({})
    try {
      await login(form.email, form.password)
      navigate('/dashboard')
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 401) {
        setErrors({ general: 'Correo o contraseña incorrectos.' })
      } else {
        setErrors({ general: 'Ocurrió un error. Intenta nuevamente.' })
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="card flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-gray-900">Iniciar sesión</h2>

      {errors.general && (
        <div role="alert" className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {errors.general}
        </div>
      )}

      <Input
        label="Correo electrónico"
        type="email"
        id="email"
        autoComplete="email"
        value={form.email}
        onChange={(e) => setForm({ ...form, email: e.target.value })}
        error={errors.email}
        placeholder="tucorreo@ejemplo.com"
      />

      <Input
        label="Contraseña"
        type="password"
        id="password"
        autoComplete="current-password"
        value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })}
        error={errors.password}
        placeholder="Tu contraseña"
      />

      <Button type="submit" isLoading={isLoading} className="w-full mt-2">
        Entrar
      </Button>

      <p className="text-sm text-center text-gray-500">
        ¿No tienes cuenta?{' '}
        <Link to="/registro" className="text-blue-600 hover:underline font-medium">
          Regístrate aquí
        </Link>
      </p>
    </form>
  )
}
