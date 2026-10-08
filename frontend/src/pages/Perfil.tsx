import { useState } from 'react'
import Aviso from '@/components/common/Aviso'
import Button from '@/components/common/Button'
import EncabezadoPagina from '@/components/common/EncabezadoPagina'
import Input from '@/components/common/Input'
import Apariencia from '@/components/perfil/Apariencia'
import FormCambioPassword from '@/components/perfil/FormCambioPassword'
import FormEliminarCuenta from '@/components/perfil/FormEliminarCuenta'
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
    <>
      <main className="mx-auto max-w-2xl space-y-5 px-4 py-6 pb-16">
        <EncabezadoPagina titulo="Mi perfil" />

        <section className="card space-y-4">
          <div className="flex items-center gap-4">
            <span
              aria-hidden="true"
              className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-marca text-2xl font-extrabold text-white"
            >
              {user.nombre.trim().charAt(0).toUpperCase()}
            </span>
            <div className="min-w-0">
              <p className="truncate text-lg font-bold text-texto">{user.nombre}</p>
              <h2 className="text-sm font-semibold text-texto-2">Datos de la cuenta</h2>
            </div>
          </div>
          <dl className="grid grid-cols-[auto,1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-texto-2">Correo electrónico</dt>
            <dd className="text-texto break-all">{user.email}</dd>
            <dt className="text-texto-2">Rol</dt>
            <dd className="text-texto">{user.role === 'administrador' ? 'Administrador' : 'Usuario'}</dd>
          </dl>
          <p className="text-xs text-texto-3">El correo electrónico no se puede modificar.</p>
        </section>

        <form onSubmit={guardar} noValidate className="card flex flex-col gap-4">
          <h2 className="text-lg font-bold text-texto">Editar nombre</h2>
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
          {exito && <Aviso tipo="exito">Tu nombre se actualizó correctamente.</Aviso>}
          <Button type="submit" isLoading={guardando} className="self-start">
            Guardar cambios
          </Button>
        </form>

        <Apariencia />

        <FormCambioPassword />

        <FormEliminarCuenta />
      </main>
    </>
  )
}
