import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileUp, Lightbulb } from 'lucide-react'
import { analisisApi } from '@/api/analisis'
import { ingestaApi } from '@/api/ingesta'
import Aviso from '@/components/common/Aviso'
import Button from '@/components/common/Button'
import VistaPreviaTexto from '@/components/ingesta/VistaPreviaTexto'
import type { IngestaResponse } from '@/types/ingesta'
import { MENSAJE_LIMITE_SOLICITUDES, esLimiteDeSolicitudes } from '@/utils/errores'
import { MAX_TEXTO, MIN_TEXTO, validarArchivo, validarTextoPolítica } from '@/utils/validators'

type Pestana = 'texto' | 'url' | 'archivo'

const ETIQUETA_PESTANA: Record<Pestana, string> = {
  texto: 'Pegar texto',
  url: 'Desde URL',
  archivo: 'Desde archivo',
}

const PASOS = ['Pega o sube', 'Revisa el texto', 'Resultados']

const MIN_CHARS = MIN_TEXTO
const MAX_CHARS = MAX_TEXTO

function mensajeDeError(err: unknown): string {
  // detail puede ser un texto (errores del servicio) o una lista (validación
  // del esquema); solo el texto se muestra tal cual.
  const detalle = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
  if (esLimiteDeSolicitudes(err)) return MENSAJE_LIMITE_SOLICITUDES
  return typeof detalle === 'string' ? detalle : 'Ocurrió un error. Intenta de nuevo.'
}

/** Pasos del análisis: el actual se marca con color y aria-current. */
function Pasos({ actual }: { actual: number }) {
  return (
    <ol aria-label="Pasos del análisis" className="mb-4 grid grid-cols-3 gap-2">
      {PASOS.map((paso, i) => {
        const hecho = i <= actual
        return (
          <li key={paso} aria-current={i === actual ? 'step' : undefined} className="flex flex-col gap-1.5">
            <span className={`h-1.5 rounded-full ${hecho ? 'bg-marca' : 'bg-borde-fuerte'}`} />
            <span className={`text-xs ${hecho ? 'font-bold text-marca-texto' : 'font-semibold text-texto-2'}`}>
              {i + 1} · {paso}
            </span>
          </li>
        )
      })}
    </ol>
  )
}

export default function IngestaForm() {
  const navigate = useNavigate()
  const [pestana, setPestana] = useState<Pestana>('texto')
  const [texto, setTexto] = useState('')
  const [url, setUrl] = useState('')
  const [archivo, setArchivo] = useState<File | null>(null)
  // Al cancelar se remonta el selector de archivo para vaciarlo.
  const [claveArchivo, setClaveArchivo] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [vistaPrevia, setVistaPrevia] = useState<IngestaResponse | null>(null)
  const [iniciando, setIniciando] = useState(false)
  const [errorInicio, setErrorInicio] = useState<string | null>(null)

  const chars = texto.length
  const charColor = (chars > 0 && chars < MIN_CHARS) || chars > MAX_CHARS ? 'text-riesgo-alto' : 'text-texto-2'

  // Paso 1: obtener y normalizar el texto; el análisis aún no se inicia.
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const errorTexto = pestana === 'texto' ? validarTextoPolítica(texto) : null
    if (errorTexto) {
      setError(errorTexto)
      return
    }
    if (pestana === 'url' && !url.trim()) {
      setError('Por favor ingresa una URL válida.')
      return
    }
    if (pestana === 'archivo') {
      const errorArchivo = archivo ? validarArchivo(archivo) : 'Selecciona un archivo PDF o TXT.'
      if (errorArchivo) {
        setError(errorArchivo)
        return
      }
    }

    setLoading(true)
    try {
      const { data } =
        pestana === 'texto'
          ? await ingestaApi.enviarTexto(texto)
          : pestana === 'url'
            ? await ingestaApi.enviarURL(url.trim())
            : await ingestaApi.enviarArchivo(archivo as File)
      setErrorInicio(null)
      setVistaPrevia(data)
    } catch (err: unknown) {
      setError(mensajeDeError(err))
    } finally {
      setLoading(false)
    }
  }

  // Paso 2: solo al confirmar se inicia el análisis (en segundo plano).
  const confirmar = async () => {
    if (!vistaPrevia) return
    setIniciando(true)
    setErrorInicio(null)
    try {
      // Con un texto dudoso, el botón solo se habilita tras marcar la confirmación (RN-18).
      const confirmaPolitica = vistaPrevia.deteccion?.resultado === 'dudosa'
      const { data: iniciado } = await analisisApi.iniciar(vistaPrevia.texto_procesado, confirmaPolitica)
      navigate(`/resultados/${iniciado.id_analisis}`)
    } catch (err: unknown) {
      setErrorInicio(mensajeDeError(err))
      setIniciando(false)
    }
  }

  // Corregir: vuelve al formulario conservando lo ingresado.
  const corregir = () => setVistaPrevia(null)

  // Cancelar: descarta el texto obtenido y lo ingresado.
  const cancelar = () => {
    setVistaPrevia(null)
    setTexto('')
    setUrl('')
    setArchivo(null)
    setClaveArchivo((clave) => clave + 1)
    setError(null)
  }

  if (vistaPrevia) {
    return (
      <>
        <Pasos actual={1} />
        <div className="card">
          <VistaPreviaTexto
            resultado={vistaPrevia}
            iniciando={iniciando}
            error={errorInicio}
            onConfirmar={confirmar}
            onCorregir={corregir}
            onCancelar={cancelar}
          />
        </div>
      </>
    )
  }

  return (
    <>
      <Pasos actual={0} />
      <div className="card space-y-5 p-4 sm:p-6">
        <div
          role="tablist"
          aria-label="Cómo quieres ingresar la política"
          className="grid grid-cols-3 gap-1 rounded-2xl bg-superficie-2 p-1"
        >
          {(['texto', 'url', 'archivo'] as Pestana[]).map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={pestana === tab}
              onClick={() => { setPestana(tab); setError(null) }}
              className={`min-h-[44px] rounded-xl px-2 text-sm font-bold transition-colors ${
                pestana === tab ? 'bg-superficie text-texto shadow-sm dark:bg-borde' : 'text-texto-2 hover:text-texto'
              }`}
            >
              {ETIQUETA_PESTANA[tab]}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {pestana === 'texto' ? (
            <div className="space-y-1.5">
              <label htmlFor="texto-politica" className="text-sm font-semibold text-texto">
                Texto de la política
              </label>
              <textarea
                id="texto-politica"
                value={texto}
                onChange={(e) => { setTexto(e.target.value); if (error) setError(null) }}
                rows={10}
                placeholder="Pega aquí el texto completo de la política de privacidad..."
                className="input-field min-h-[220px] resize-y leading-relaxed"
                disabled={loading}
              />
              <p className={`text-right text-sm ${charColor}`}>
                {chars.toLocaleString()} / {MAX_CHARS.toLocaleString()} caracteres
                {chars > 0 && chars < MIN_CHARS && <span className="ml-2">(mínimo {MIN_CHARS})</span>}
              </p>
            </div>
          ) : pestana === 'archivo' ? (
            <div className="space-y-1.5">
              <label
                htmlFor="archivo-politica"
                className="flex cursor-pointer flex-col items-center gap-2.5 rounded-2xl border-2 border-dashed border-marca-borde bg-marca-suave/40 px-4 py-8 text-center focus-within:ring-2 focus-within:ring-marca"
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-marca-suave text-marca-texto">
                  <FileUp size={24} aria-hidden="true" />
                </span>
                <span className="text-base font-bold text-texto">Archivo de la política (PDF o TXT, máximo 5 MB)</span>
                <span className="text-sm text-texto-2">
                  {archivo
                    ? `${archivo.name} · ${(archivo.size / 1024).toFixed(0)} KB`
                    : 'Toca para elegirlo. Solo guardamos el texto, no el archivo.'}
                </span>
                <input
                  key={claveArchivo}
                  id="archivo-politica"
                  type="file"
                  accept=".pdf,.txt,application/pdf,text/plain"
                  onChange={(e) => { setArchivo(e.target.files?.[0] ?? null); if (error) setError(null) }}
                  className="sr-only"
                  disabled={loading}
                />
              </label>
            </div>
          ) : (
            <div className="space-y-1.5">
              <label htmlFor="url-politica" className="text-sm font-semibold text-texto">
                Enlace de la política de privacidad
              </label>
              <input
                id="url-politica"
                type="url"
                inputMode="url"
                value={url}
                onChange={(e) => { setUrl(e.target.value); if (error) setError(null) }}
                placeholder="https://ejemplo.com/politica-de-privacidad"
                className="input-field"
                disabled={loading}
              />
              <p className="text-sm text-texto-2">
                Busca «Política de privacidad» al pie de la página de la app o del sitio y copia ese enlace.
              </p>
            </div>
          )}

          {error && <Aviso tipo="error">{error}</Aviso>}
          {loading && <Aviso tipo="info">Procesando texto...</Aviso>}

          <Button
            type="submit"
            isLoading={loading}
            disabled={pestana === 'texto' && (chars < MIN_CHARS || chars > MAX_CHARS)}
            className="w-full"
          >
            Revisar texto
          </Button>
        </form>
      </div>

      <aside aria-label="Consejo" className="mt-4 flex items-start gap-3 rounded-2xl bg-riesgo-bajo/10 p-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-superficie text-riesgo-bajo">
          <Lightbulb size={20} aria-hidden="true" />
        </span>
        <div>
          <p className="font-bold text-riesgo-bajo">¡Buena decisión!</p>
          <p className="text-sm leading-relaxed text-texto">
            Leer qué datos pide una app antes de aceptar es la mejor forma de cuidar tu privacidad.
          </p>
        </div>
      </aside>
    </>
  )
}
