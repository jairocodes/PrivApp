import { useEffect, useState } from 'react'
import { Search, Users } from 'lucide-react'
import { adminApi } from '@/api/admin'
import Aviso from '@/components/common/Aviso'
import Cargando from '@/components/common/Cargando'
import EncabezadoPagina from '@/components/common/EncabezadoPagina'
import EstadoVacio from '@/components/common/EstadoVacio'
import Insignia from '@/components/common/Insignia'
import DialogoConfirmacion from '@/components/common/DialogoConfirmacion'
import Paginacion from '@/components/common/Paginacion'
import { useAuth } from '@/hooks/useAuth'
import { useUsuariosAdmin } from '@/hooks/useUsuariosAdmin'
import type { UsuarioAdmin } from '@/types/admin'

export default function AdminUsuarios() {
  const { user } = useAuth()
  const { items, total, page, pageSize, isLoading, error, cargar, reemplazar } = useUsuariosAdmin()
  const [texto, setTexto] = useState('')
  const [pendiente, setPendiente] = useState<UsuarioAdmin | null>(null)
  const [procesando, setProcesando] = useState(false)
  const [errorCambio, setErrorCambio] = useState<string | null>(null)

  const abrirConfirmacion = (usuario: UsuarioAdmin) => {
    setErrorCambio(null)
    setPendiente(usuario)
  }

  const confirmarCambio = async () => {
    if (!pendiente) return
    setProcesando(true)
    setErrorCambio(null)
    try {
      const { data } = await adminApi.cambiarEstadoUsuario(pendiente.id, !pendiente.is_active)
      reemplazar(data)
      setPendiente(null)
    } catch (err: unknown) {
      const detalle = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setErrorCambio(detalle ?? 'No fue posible cambiar el estado de la cuenta.')
    } finally {
      setProcesando(false)
    }
  }

  useEffect(() => {
    cargar(1, '')
  }, [])

  const totalPaginas = Math.max(1, Math.ceil(total / pageSize))

  const buscar = (e: React.FormEvent) => {
    e.preventDefault()
    cargar(1, texto.trim())
  }

  return (
    <>

      <main className="mx-auto max-w-3xl px-4 py-6 pb-16">
        <EncabezadoPagina
          titulo="Usuarios"
          subtitulo="Cuentas registradas. No se muestra el contenido de sus análisis."
          volverA="/admin"
          etiquetaVolver="Volver a administración"
        />

        <form onSubmit={buscar} role="search" className="flex gap-2 mb-5">
          <label htmlFor="busqueda-usuarios" className="sr-only">
            Buscar por nombre o correo
          </label>
          <input
            id="busqueda-usuarios"
            type="search"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Buscar por nombre o correo"
            className="input-field flex-1"
          />
          <button type="submit" className="btn-primary inline-flex items-center gap-1 text-sm">
            <Search size={16} aria-hidden="true" />
            Buscar
          </button>
        </form>

        {isLoading && <Cargando mensaje="Cargando usuarios..." />}
        {error && !isLoading && (
          <Aviso tipo="error">{error}</Aviso>
        )}
        {!isLoading && !error && items.length === 0 && (
          <EstadoVacio icono={Users} mensaje="No se encontraron usuarios." />
        )}

        {!isLoading && !error && items.length > 0 && (
          <>
            <ul className="space-y-3">
              {items.map((usuario) => (
                <FilaUsuario
                  key={usuario.id}
                  usuario={usuario}
                  esCuentaPropia={usuario.id === user?.id}
                  onCambiarEstado={() => abrirConfirmacion(usuario)}
                />
              ))}
            </ul>

            <Paginacion page={page} totalPaginas={totalPaginas} onCambiarPagina={(pagina) => cargar(pagina)} />
          </>
        )}
      </main>

      <DialogoConfirmacion
        abierto={pendiente !== null}
        titulo={
          pendiente?.is_active
            ? `¿Desactivar la cuenta de ${pendiente.nombre}?`
            : `¿Activar la cuenta de ${pendiente?.nombre ?? ''}?`
        }
        mensaje={
          pendiente?.is_active
            ? 'La persona no podrá iniciar sesión y se cerrarán todas sus sesiones activas.'
            : 'La persona podrá volver a iniciar sesión.'
        }
        textoConfirmar={pendiente?.is_active ? 'Desactivar' : 'Activar'}
        procesando={procesando}
        error={errorCambio}
        onConfirmar={confirmarCambio}
        onCancelar={() => setPendiente(null)}
      />
    </>
  )
}

function FilaUsuario({
  usuario,
  esCuentaPropia,
  onCambiarEstado,
}: {
  usuario: UsuarioAdmin
  esCuentaPropia: boolean
  onCambiarEstado: () => void
}) {
  const fecha = new Date(usuario.created_at).toLocaleDateString('es-GT', {
    day: '2-digit', month: 'short', year: 'numeric',
  })

  return (
    <li className="flex items-center justify-between gap-3 rounded-2xl border border-borde bg-superficie p-4">
      <div className="min-w-0">
        <p className="truncate font-bold text-texto">{usuario.nombre}</p>
        <p className="text-sm text-texto-2 truncate">{usuario.email}</p>
        <p className="text-xs text-texto-3 mt-1">
          {usuario.role === 'administrador' ? 'Administrador' : 'Usuario'} · Registrado el {fecha}
        </p>
      </div>
      <div className="flex flex-col items-end gap-2 shrink-0">
        <Insignia tono={usuario.is_active ? 'bajo' : 'neutro'}>{usuario.is_active ? 'Activa' : 'Desactivada'}</Insignia>
        {esCuentaPropia ? (
          <span className="text-xs text-texto-3">Tu cuenta</span>
        ) : (
          <button
            type="button"
            onClick={onCambiarEstado}
            aria-label={`${usuario.is_active ? 'Desactivar' : 'Activar'} la cuenta de ${usuario.nombre}`}
            className={`inline-flex min-h-[40px] items-center rounded-xl border px-3 text-sm font-semibold transition-colors ${
              usuario.is_active
                ? 'border-riesgo-alto/30 text-riesgo-alto hover:bg-riesgo-alto/10'
                : 'border-marca-borde text-marca-texto hover:bg-marca-suave'
            }`}
          >
            {usuario.is_active ? 'Desactivar' : 'Activar'}
          </button>
        )}
      </div>
    </li>
  )
}
