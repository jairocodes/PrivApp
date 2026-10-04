import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Input from '@/components/common/Input'
import DialogoConfirmacion from '@/components/common/DialogoConfirmacion'
import { useAuth } from '@/hooks/useAuth'
import { detalleDeError } from '@/utils/errores'

export const MENSAJE_CUENTA_ELIMINADA = 'Tu cuenta y todos tus análisis se eliminaron definitivamente.'
// Mismo texto que PasswordIncorrectaError en el servidor.
const MENSAJE_PASSWORD_INCORRECTA = 'La contraseña es incorrecta.'
const MENSAJE_ERROR_GENERICO = 'No fue posible eliminar tu cuenta. Intenta nuevamente.'

export default function FormEliminarCuenta() {
  const { eliminarCuenta } = useAuth()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [errorPassword, setErrorPassword] = useState<string | null>(null)
  const [errorDialogo, setErrorDialogo] = useState<string | null>(null)
  const [confirmando, setConfirmando] = useState(false)
  const [eliminando, setEliminando] = useState(false)

  const solicitar = (e: React.FormEvent) => {
    e.preventDefault()
    if (!password) {
      setErrorPassword('Ingresa tu contraseña para confirmar.')
      return
    }
    setErrorPassword(null)
    setErrorDialogo(null)
    setConfirmando(true)
  }

  const eliminar = async () => {
    setEliminando(true)
    try {
      await eliminarCuenta(password)
      navigate('/login', { replace: true, state: { mensaje: MENSAJE_CUENTA_ELIMINADA } })
    } catch (err: unknown) {
      const estado = (err as { response?: { status?: number } }).response?.status
      const detalle = detalleDeError(err, MENSAJE_ERROR_GENERICO)
      if (estado === 400 && detalle === MENSAJE_PASSWORD_INCORRECTA) {
        // La contraseña se corrige en el formulario, no en el diálogo.
        setConfirmando(false)
        setErrorPassword(detalle)
      } else {
        // 409 (análisis en curso), 400 (único administrador) y 429 traen un mensaje claro.
        setErrorDialogo(estado === 400 || estado === 409 || estado === 429 ? detalle : MENSAJE_ERROR_GENERICO)
      }
    } finally {
      setEliminando(false)
    }
  }

  return (
    <form onSubmit={solicitar} noValidate className="card flex flex-col gap-4 border-riesgo-alto/30">
      <h2 className="text-lg font-bold text-riesgo-alto">Eliminar mi cuenta</h2>
      <p className="text-sm text-texto-2 leading-relaxed">
        Se eliminarán de forma definitiva tu cuenta y todos tus análisis. Esta acción no se puede
        deshacer.
      </p>
      <Input
        label="Contraseña"
        type="password"
        id="password-eliminar"
        autoComplete="current-password"
        value={password}
        onChange={(e) => {
          setPassword(e.target.value)
          setErrorPassword(null)
        }}
        error={errorPassword ?? undefined}
      />
      <button type="submit" className="btn-secondary text-sm self-start text-riesgo-alto">
        Eliminar mi cuenta
      </button>

      <DialogoConfirmacion
        abierto={confirmando}
        titulo="¿Eliminar tu cuenta?"
        mensaje="Se eliminarán tu cuenta y todos tus análisis. Esta acción es definitiva y no se puede deshacer."
        textoConfirmar="Eliminar definitivamente"
        procesando={eliminando}
        error={errorDialogo}
        onConfirmar={eliminar}
        onCancelar={() => setConfirmando(false)}
      />
    </form>
  )
}
