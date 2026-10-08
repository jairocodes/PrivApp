import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import Button from '@/components/common/Button'
import Input from '@/components/common/Input'
import { MENSAJE_LIMITE_SOLICITUDES, esLimiteDeSolicitudes } from '@/utils/errores'
import Aviso from '@/components/common/Aviso'

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
      } else if (esLimiteDeSolicitudes(err)) {
        setErrors({ general: MENSAJE_LIMITE_SOLICITUDES })
      } else {
        setErrors({ general: 'Ocurrió un error. Intenta nuevamente.' })
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="card flex flex-col gap-4 sm:p-8">
      <h2 className="text-xl font-bold text-texto">Iniciar sesión</h2>

      {errors.general && (
        <Aviso tipo="error">{errors.general}</Aviso>
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

      <p className="text-sm text-center text-texto-2">
        ¿No tienes cuenta?{' '}
        <Link to="/registro" className="font-semibold text-marca-texto hover:underline">
          Regístrate aquí
        </Link>
      </p>
    </form>
  )
}
