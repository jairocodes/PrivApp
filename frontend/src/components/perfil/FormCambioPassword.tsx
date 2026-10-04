import { useState } from 'react'
import Button from '@/components/common/Button'
import Input from '@/components/common/Input'
import { useAuth } from '@/hooks/useAuth'
import { MENSAJE_LIMITE_SOLICITUDES, esLimiteDeSolicitudes } from '@/utils/errores'
import { validarPassword } from '@/utils/validators'
import Aviso from '@/components/common/Aviso'

interface Campos {
  actual: string
  nueva: string
  confirmacion: string
}

interface Errores {
  actual?: string
  nueva?: string
  confirmacion?: string
  general?: string
}

const VACIO: Campos = { actual: '', nueva: '', confirmacion: '' }

export default function FormCambioPassword() {
  const { cambiarPassword } = useAuth()
  const [campos, setCampos] = useState<Campos>(VACIO)
  const [errores, setErrores] = useState<Errores>({})
  const [exito, setExito] = useState(false)
  const [guardando, setGuardando] = useState(false)

  const validar = (): boolean => {
    const nuevos: Errores = {}
    if (!campos.actual) nuevos.actual = 'Ingresa tu contraseña actual.'
    const errorNueva = validarPassword(campos.nueva)
    if (errorNueva) nuevos.nueva = errorNueva
    else if (campos.nueva === campos.actual)
      nuevos.nueva = 'La nueva contraseña debe ser distinta de la actual.'
    if (campos.nueva !== campos.confirmacion)
      nuevos.confirmacion = 'La confirmación no coincide con la nueva contraseña.'
    setErrores(nuevos)
    return Object.keys(nuevos).length === 0
  }

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setExito(false)
    if (!validar()) return

    setGuardando(true)
    try {
      await cambiarPassword({
        password_actual: campos.actual,
        password_nueva: campos.nueva,
        confirmar_password: campos.confirmacion,
      })
      setCampos(VACIO)
      setExito(true)
    } catch (err: unknown) {
      const respuesta = (err as { response?: { status?: number; data?: { detail?: unknown } } }).response
      const detalle = respuesta?.data?.detail
      if (esLimiteDeSolicitudes(err)) {
        setErrores({ general: MENSAJE_LIMITE_SOLICITUDES })
      } else if (respuesta?.status === 400 && typeof detalle === 'string') {
        setErrores(detalle.includes('actual es incorrecta') ? { actual: detalle } : { nueva: detalle })
      } else {
        setErrores({ general: 'No fue posible cambiar tu contraseña. Intenta nuevamente.' })
      }
    } finally {
      setGuardando(false)
    }
  }

  const actualizar = (campo: keyof Campos) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setCampos({ ...campos, [campo]: e.target.value })
    setExito(false)
  }

  return (
    <form onSubmit={enviar} noValidate className="card flex flex-col gap-4">
      <h2 className="text-base font-semibold text-texto">Cambiar contraseña</h2>

      {errores.general && (
        <Aviso tipo="error">{errores.general}</Aviso>
      )}

      <Input
        label="Contraseña actual"
        type="password"
        id="password-actual"
        autoComplete="current-password"
        value={campos.actual}
        onChange={actualizar('actual')}
        error={errores.actual}
      />
      <div className="flex flex-col gap-1">
        <Input
          label="Nueva contraseña"
          type="password"
          id="password-nueva"
          autoComplete="new-password"
          value={campos.nueva}
          onChange={actualizar('nueva')}
          error={errores.nueva}
        />
        <p className="text-xs text-texto-3 mt-0.5">Mínimo 8 caracteres, una mayúscula y un número.</p>
      </div>
      <Input
        label="Confirmar nueva contraseña"
        type="password"
        id="password-confirmacion"
        autoComplete="new-password"
        value={campos.confirmacion}
        onChange={actualizar('confirmacion')}
        error={errores.confirmacion}
      />

      {exito && (
        <p role="status" className="text-sm text-riesgo-bajo">
          Tu contraseña se actualizó. Se cerraron las sesiones abiertas en otros dispositivos.
        </p>
      )}

      <Button type="submit" isLoading={guardando} className="self-start">
        Cambiar contraseña
      </Button>
    </form>
  )
}
