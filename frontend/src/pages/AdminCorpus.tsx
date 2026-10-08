import { useEffect, useState } from 'react'
import { Library } from 'lucide-react'
import { adminApi } from '@/api/admin'
import FormCargaDocumento from '@/components/admin/FormCargaDocumento'
import Aviso from '@/components/common/Aviso'
import Cargando from '@/components/common/Cargando'
import EncabezadoPagina from '@/components/common/EncabezadoPagina'
import EstadoVacio from '@/components/common/EstadoVacio'
import Insignia from '@/components/common/Insignia'
import DialogoConfirmacion from '@/components/common/DialogoConfirmacion'
import type { DocumentoCargado, DocumentoCorpus } from '@/types/admin'

export const ETIQUETA_JURISDICCION: Record<string, string> = {
  guatemala: 'Guatemala',
  internacional: 'Internacional',
  estandar_tecnico: 'Estándar técnico',
}

function mensajeDeError(err: unknown, porDefecto: string): string {
  const detalle = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
  return typeof detalle === 'string' ? detalle : porDefecto
}

export default function AdminCorpus() {
  const [documentos, setDocumentos] = useState<DocumentoCorpus[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendiente, setPendiente] = useState<DocumentoCorpus | null>(null)
  const [procesando, setProcesando] = useState(false)
  const [errorCambio, setErrorCambio] = useState<string | null>(null)

  const cargar = async () => {
    setCargando(true)
    setError(null)
    try {
      const { data } = await adminApi.listarCorpus()
      setDocumentos(data.documentos)
    } catch {
      setError('No fue posible cargar el corpus normativo.')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [])

  const agregarCargado = ({ fragmentos_insertados: _i, fragmentos_duplicados: _d, ...documento }: DocumentoCargado) => {
    setDocumentos((actuales) =>
      [...actuales, documento].sort((a, b) => a.documento_fuente.localeCompare(b.documento_fuente)),
    )
  }

  const confirmarCambio = async () => {
    if (!pendiente) return
    setProcesando(true)
    setErrorCambio(null)
    try {
      const { data } = await adminApi.cambiarEstadoDocumento(pendiente.documento_fuente, !pendiente.activo)
      setDocumentos((actuales) =>
        actuales.map((d) => (d.documento_fuente === data.documento_fuente ? data : d)),
      )
      setPendiente(null)
    } catch (err: unknown) {
      setErrorCambio(mensajeDeError(err, 'No fue posible cambiar el estado del documento.'))
    } finally {
      setProcesando(false)
    }
  }

  return (
    <>

      <main className="mx-auto max-w-3xl space-y-5 px-4 py-6 pb-16">
        <EncabezadoPagina
          titulo="Corpus normativo"
          subtitulo="Documentos con los que se respaldan los hallazgos de los análisis."
          volverA="/admin"
          etiquetaVolver="Volver a administración"
        />

        <FormCargaDocumento onCargado={agregarCargado} />

        {cargando && <Cargando mensaje="Cargando documentos..." />}
        {error && !cargando && (
          <Aviso tipo="error">{error}</Aviso>
        )}
        {!cargando && !error && documentos.length === 0 && (
          <EstadoVacio icono={Library} mensaje="El corpus no tiene documentos cargados." />
        )}

        {!cargando && !error && documentos.length > 0 && (
          <ul className="space-y-3">
            {documentos.map((documento) => (
              <FilaDocumento
                key={documento.documento_fuente}
                documento={documento}
                onCambiarEstado={() => {
                  setErrorCambio(null)
                  setPendiente(documento)
                }}
              />
            ))}
          </ul>
        )}
      </main>

      <DialogoConfirmacion
        abierto={pendiente !== null}
        titulo={
          pendiente?.activo
            ? `¿Desactivar «${pendiente.documento_fuente}»?`
            : `¿Activar «${pendiente?.documento_fuente ?? ''}»?`
        }
        mensaje={
          pendiente?.activo
            ? 'Sus fragmentos dejarán de considerarse en los análisis nuevos. Los análisis ya realizados no cambian.'
            : 'Sus fragmentos volverán a considerarse en los análisis nuevos.'
        }
        textoConfirmar={pendiente?.activo ? 'Desactivar' : 'Activar'}
        procesando={procesando}
        error={errorCambio}
        onConfirmar={confirmarCambio}
        onCancelar={() => setPendiente(null)}
      />
    </>
  )
}

function FilaDocumento({
  documento,
  onCambiarEstado,
}: {
  documento: DocumentoCorpus
  onCambiarEstado: () => void
}) {
  const fecha = documento.fecha_carga
    ? new Date(documento.fecha_carga).toLocaleDateString('es-GT', {
        day: '2-digit', month: 'short', year: 'numeric',
      })
    : 'sin fecha'

  return (
    <li className="flex items-center justify-between gap-3 rounded-2xl border border-borde bg-superficie p-4">
      <div className="min-w-0">
        <p className="break-words font-bold text-texto">{documento.documento_fuente}</p>
        <p className="text-xs text-texto-2 mt-1">
          {ETIQUETA_JURISDICCION[documento.jurisdiccion] ?? documento.jurisdiccion} ·{' '}
          {documento.fragmentos.toLocaleString('es-GT')} fragmentos · Cargado el {fecha}
        </p>
      </div>
      <div className="flex flex-col items-end gap-2 shrink-0">
        <Insignia tono={documento.activo ? 'bajo' : 'neutro'}>{documento.activo ? 'Activo' : 'Desactivado'}</Insignia>
        <button
          type="button"
          onClick={onCambiarEstado}
          aria-label={`${documento.activo ? 'Desactivar' : 'Activar'} ${documento.documento_fuente}`}
          className={`inline-flex min-h-[40px] items-center rounded-xl border px-3 text-sm font-semibold transition-colors ${
            documento.activo
              ? 'border-riesgo-alto/30 text-riesgo-alto hover:bg-riesgo-alto/10'
              : 'border-marca-borde text-marca-texto hover:bg-marca-suave'
          }`}
        >
          {documento.activo ? 'Desactivar' : 'Activar'}
        </button>
      </div>
    </li>
  )
}
