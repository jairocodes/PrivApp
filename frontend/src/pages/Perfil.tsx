import { useState } from 'react'
import Navbar from '@/components/common/Navbar'
import Button from '@/components/common/Button'
import Input from '@/components/common/Input'
import { useAuth } from '@/hooks/useAuth'

const NOMBRE_MIN = 2
const NOMBRE_MAX = 100

export default function Perfil() {
  const { user, actualizarPerfil } = useAuth()
  const [nombre, setNombre] = useState(user?.nombre ?? '')
  const [error, setError] = useState<string | null>(null)
  const [exito, setExito] = useState(false)
  const [guardando, setGuardando] = useState(false)

  if (!user) return null

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault()
    setExito(false)
    const limpio = nombre.trim()
    if (limpio.length < NOMBRE_MIN) {
      setError(`El nombre debe tener al menos ${NOMBRE_MIN} caracteres.`)
      return
    }
    if (limpio.length > NOMBRE_MAX) {
      setError(`El nombre no puede superar los ${NOMBRE_MAX} caracteres.`)
      return
    }

    setError(null)
    setGuardando(true)
    try {
      await actualizarPerfil(limpio)
      setNombre(limpio)
      setExito(true)
    } catch {
      setError('No fue posible actualizar tu nombre. Intenta nuevamente.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16 space-y-5">
        <h1 className="text-xl font-bold text-gray-900">Mi perfil</h1>

        <section className="card space-y-3">
          <h2 className="text-base font-semibold text-gray-800">Datos de la cuenta</h2>
          <dl className="grid grid-cols-[auto,1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-gray-500">Correo electrónico</dt>
            <dd className="text-gray-900 break-all">{user.email}</dd>
            <dt className="text-gray-500">Rol</dt>
            <dd className="text-gray-900">{user.role === 'administrador' ? 'Administrador' : 'Usuario'}</dd>
          </dl>
          <p className="text-xs text-gray-400">El correo electrónico no se puede modificar.</p>
        </section>

        <form onSubmit={guardar} noValidate className="card flex flex-col gap-4">
          <h2 className="text-base font-semibold text-gray-800">Editar nombre</h2>
          <Input
            label="Nombre completo"
            id="nombre"
            autoComplete="name"
            value={nombre}
            maxLength={NOMBRE_MAX}
            onChange={(e) => {
              setNombre(e.target.value)
              setExito(false)
            }}
            error={error ?? undefined}
          />
          {exito && (
            <p role="status" className="text-sm text-riesgo-bajo">
              Tu nombre se actualizó correctamente.
            </p>
          )}
          <Button type="submit" isLoading={guardando} className="self-start">
            Guardar cambios
          </Button>
        </form>
      </main>
    </div>
  )
}
