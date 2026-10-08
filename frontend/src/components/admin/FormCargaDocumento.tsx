import { useState } from 'react'
import { adminApi } from '@/api/admin'
import Button from '@/components/common/Button'
import type { DocumentoCargado, Jurisdiccion } from '@/types/admin'
import { validarArchivo } from '@/utils/validators'
import Aviso from '@/components/common/Aviso'

interface Props {
  onCargado: (documento: DocumentoCargado) => void
}

const OPCIONES: { valor: Jurisdiccion; etiqueta: string }[] = [
  { valor: 'guatemala', etiqueta: 'Guatemala' },
  { valor: 'internacional', etiqueta: 'Internacional' },
  { valor: 'estandar_tecnico', etiqueta: 'Estándar técnico' },
]

export default function FormCargaDocumento({ onCargado }: Props) {
  const [archivo, setArchivo] = useState<File | null>(null)
  const [jurisdiccion, setJurisdiccion] = useState<Jurisdiccion | ''>('')
  const [claveArchivo, setClaveArchivo] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [exito, setExito] = useState<string | null>(null)
  const [cargando, setCargando] = useState(false)

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setExito(null)
    const errorArchivo = archivo ? validarArchivo(archivo) : 'Selecciona un archivo PDF o TXT.'
    if (errorArchivo) {
      setError(errorArchivo)
      return
    }
    if (!jurisdiccion) {
      setError('Selecciona la jurisdicción del documento.')
      return
    }

    setError(null)
    setCargando(true)
    try {
      const { data } = await adminApi.cargarDocumento(archivo as File, jurisdiccion)
      onCargado(data)
      setExito(
        `Se incorporó «${data.documento_fuente}» con ${data.fragmentos_insertados.toLocaleString('es-GT')} fragmentos.`,
      )
      setArchivo(null)
      setJurisdiccion('')
      setClaveArchivo((clave) => clave + 1)
    } catch (err: unknown) {
      const detalle = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
      setError(typeof detalle === 'string' ? detalle : 'No fue posible cargar el documento.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <form onSubmit={enviar} noValidate className="card flex flex-col gap-4">
      <h2 className="text-base font-semibold text-texto">Cargar documento normativo</h2>

      <div className="flex flex-col gap-1">
        <label htmlFor="documento-normativo" className="text-sm font-medium text-texto-2">
          Archivo (PDF o TXT, máximo 5 MB)
        </label>
        <input
          key={claveArchivo}
          id="documento-normativo"
          type="file"
          accept=".pdf,.txt,application/pdf,text/plain"
          onChange={(e) => {
            setArchivo(e.target.files?.[0] ?? null)
            setError(null)
          }}
          disabled={cargando}
          className="w-full text-sm text-texto-2 file:mr-3 file:rounded-lg file:border-0
                     file:bg-marca-suave file:px-4 file:py-2 file:text-marca-texto hover:file:bg-marca-suave"
        />
        <p className="text-xs text-texto-3">
          El nombre del archivo identificará al documento en el corpus. Solo se guardan sus fragmentos de texto.
        </p>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="jurisdiccion" className="text-sm font-medium text-texto-2">
          Jurisdicción
        </label>
        <select
          id="jurisdiccion"
          value={jurisdiccion}
          onChange={(e) => {
            setJurisdiccion(e.target.value as Jurisdiccion | '')
            setError(null)
          }}
          disabled={cargando}
          className="input-field"
        >
          <option value="">Selecciona una opción</option>
          {OPCIONES.map((opcion) => (
            <option key={opcion.valor} value={opcion.valor}>
              {opcion.etiqueta}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <Aviso tipo="error">{error}</Aviso>
      )}
      {cargando && (
        <p className="text-sm text-marca-texto bg-marca-suave border border-marca-borde rounded-lg p-3">
          Procesando el documento. Generar sus representaciones puede tardar varios minutos.
        </p>
      )}
      {exito && (
        <p role="status" className="text-sm text-riesgo-bajo">
          {exito}
        </p>
      )}

      <Button type="submit" isLoading={cargando} className="self-start">
        Cargar documento
      </Button>
    </form>
  )
}
