import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import Button from '@/components/common/Button'
import Input from '@/components/common/Input'
import { validarPassword } from '@/utils/validators'

interface FormState {
  nombre: string
  email: string
  password: string
  confirmPassword: string
  aceptaAviso: boolean
}

interface FormErrors {
  nombre?: string
  email?: string
  password?: string
  confirmPassword?: string
  aceptaAviso?: string
  general?: string
}

export default function RegisterForm() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState<FormState>({
    nombre: '',
    email: '',
    password: '',
    confirmPassword: '',
    aceptaAviso: false,
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)

  const validate = (): boolean => {
    const newErrors: FormErrors = {}

    if (form.nombre.trim().length < 2) newErrors.nombre = 'El nombre debe tener al menos 2 caracteres.'
    if (!form.email) newErrors.email = 'El correo es obligatorio.'

    const passwordError = validarPassword(form.password)
    if (passwordError) newErrors.password = passwordError

    if (form.password !== form.confirmPassword)
      newErrors.confirmPassword = 'Las contraseñas no coinciden.'

    if (!form.aceptaAviso)
      newErrors.aceptaAviso = 'Debes aceptar el aviso de privacidad para registrarte.'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    setIsLoading(true)
    setErrors({})
    try {
      await register(form.nombre.trim(), form.email, form.password, form.aceptaAviso)
      navigate('/dashboard')
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 409) {
        setErrors({ email: 'Este correo ya está registrado.' })
      } else {
        setErrors({ general: 'Ocurrió un error. Intenta nuevamente.' })
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="card flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-gray-900">Crear cuenta</h2>

      {errors.general && (
        <div role="alert" className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {errors.general}
        </div>
      )}

      <Input
        label="Nombre completo"
        type="text"
        id="nombre"
        autoComplete="name"
        value={form.nombre}
        onChange={(e) => setForm({ ...form, nombre: e.target.value })}
        error={errors.nombre}
        placeholder="Tu nombre"
      />

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

      <div className="flex flex-col gap-1">
        <Input
          label="Contraseña"
          type="password"
          id="password"
          autoComplete="new-password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          error={errors.password}
          placeholder="Mínimo 8 caracteres, 1 mayúscula, 1 número"
        />
        <p className="text-xs text-gray-400 mt-0.5">
          Mínimo 8 caracteres, una mayúscula y un número.
        </p>
      </div>

      <Input
        label="Confirmar contraseña"
        type="password"
        id="confirmPassword"
        autoComplete="new-password"
        value={form.confirmPassword}
        onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
        error={errors.confirmPassword}
        placeholder="Repite tu contraseña"
      />

      <div className="flex flex-col gap-1">
        <label htmlFor="aceptaAviso" className="flex items-start gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            id="aceptaAviso"
            checked={form.aceptaAviso}
            onChange={(e) => setForm({ ...form, aceptaAviso: e.target.checked })}
            aria-invalid={Boolean(errors.aceptaAviso)}
            className="mt-0.5"
          />
          <span>
            He leído y acepto el{' '}
            <Link
              to="/aviso-privacidad"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline font-medium"
            >
              aviso de privacidad
            </Link>
          </span>
        </label>
        {errors.aceptaAviso && <p className="text-sm text-red-600">{errors.aceptaAviso}</p>}
      </div>

      <Button type="submit" isLoading={isLoading} className="w-full mt-2">
        Crear cuenta
      </Button>

      <p className="text-sm text-center text-gray-500">
        ¿Ya tienes cuenta?{' '}
        <Link to="/login" className="text-blue-600 hover:underline font-medium">
          Inicia sesión
        </Link>
      </p>
    </form>
  )
}
