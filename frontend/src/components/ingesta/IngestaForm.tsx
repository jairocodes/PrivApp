import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/api/client'
import { analisisApi } from '@/api/analisis'
import Button from '@/components/common/Button'
import { MENSAJE_LIMITE_SOLICITUDES, esLimiteDeSolicitudes } from '@/utils/errores'
import { MAX_TEXTO, MIN_TEXTO, validarArchivo, validarTextoPolítica } from '@/utils/validators'

type Pestana = 'texto' | 'url' | 'archivo'

const ETIQUETA_PESTANA: Record<Pestana, string> = {
  texto: 'Pegar texto',
  url: 'Desde URL',
  archivo: 'Desde archivo',
}

const MIN_CHARS = MIN_TEXTO
const MAX_CHARS = MAX_TEXTO

interface IngestaResponse {
  texto_procesado: string
  caracteres: number
  palabras: number
  fuente: string
}

export default function IngestaForm() {
  const navigate = useNavigate()
  const [pestana, setPestana] = useState<Pestana>('texto')
  const [texto, setTexto] = useState('')
  const [url, setUrl] = useState('')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [fase, setFase] = useState<'ingesta' | 'analisis' | null>(null)

  const chars = texto.length
  const charColor =
    chars > 0 && chars < MIN_CHARS
      ? 'text-red-500'
      : chars > MAX_CHARS
      ? 'text-red-500'
      : 'text-gray-500'

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
      // Paso 1: ingesta
      setFase('ingesta')
      let textoProcesado: string
      if (pestana === 'texto') {
        const { data } = await apiClient.post<IngestaResponse>('/api/ingesta/texto', { texto })
        textoProcesado = data.texto_procesado
      } else if (pestana === 'url') {
        const { data } = await apiClient.post<IngestaResponse>('/api/ingesta/url', { url: url.trim() })
        textoProcesado = data.texto_procesado
      } else {
        const formulario = new FormData()
        formulario.append('archivo', archivo as File)
        // Sin esta cabecera axios convertiría el FormData a JSON (el cliente usa
        // application/json por defecto); el navegador completa el separador.
        const { data } = await apiClient.post<IngestaResponse>('/api/ingesta/archivo', formulario, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        textoProcesado = data.texto_procesado
      }

      // Paso 2: inicia el análisis (se procesa en segundo plano)
      setFase('analisis')
      const { data: iniciado } = await analisisApi.iniciar(textoProcesado)

      // Navegar a la vista de progreso / resultados
      navigate(`/resultados/${iniciado.id_analisis}`)
    } catch (err: unknown) {
      // detail puede ser un texto (errores del servicio) o una lista (validación
      // del esquema); solo el texto se muestra tal cual.
      const detalle = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
      setError(
        esLimiteDeSolicitudes(err)
          ? MENSAJE_LIMITE_SOLICITUDES
          : typeof detalle === 'string'
            ? detalle
            : 'Ocurrió un error. Intenta de nuevo.',
      )
    } finally {
      setLoading(false)
      setFase(null)
    }
  }

  const mensajeCarga =
    fase === 'ingesta'
      ? 'Procesando texto...'
      : fase === 'analisis'
      ? 'Iniciando análisis...'
      : 'Cargando...'

  return (
    <div className="card max-w-2xl mx-auto">
      <h2 className="text-xl font-bold text-gray-800 mb-4">
        Analizar política de privacidad
      </h2>

      {/* Pestañas */}
      <div className="flex border-b border-gray-200 mb-6" role="tablist">
        {(['texto', 'url', 'archivo'] as Pestana[]).map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={pestana === tab}
            onClick={() => { setPestana(tab); setError(null) }}
            className={`px-5 py-2 text-sm font-medium capitalize transition-colors
              ${pestana === tab
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
              }`}
          >
            {ETIQUETA_PESTANA[tab]}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} noValidate>
        {pestana === 'texto' ? (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Pega el contenido de la política de privacidad
            </label>
            <textarea
              value={texto}
              onChange={(e) => { setTexto(e.target.value); if (error) setError(null) }}
              rows={12}
              placeholder="Pega aquí el texto completo de la política de privacidad..."
              className="w-full border border-gray-300 rounded-lg p-3 text-sm
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
              disabled={loading}
            />
            <p className={`text-xs mt-1 text-right ${charColor}`}>
              {chars.toLocaleString()} / {MAX_CHARS.toLocaleString()} caracteres
              {chars > 0 && chars < MIN_CHARS && (
                <span className="ml-2">(mínimo {MIN_CHARS})</span>
              )}
            </p>
          </div>
        ) : pestana === 'archivo' ? (
          <div className="mb-4">
            <label htmlFor="archivo-politica" className="block text-sm font-medium text-gray-700 mb-1">
              Archivo de la política (PDF o TXT, máximo 5 MB)
            </label>
            <input
              id="archivo-politica"
              type="file"
              accept=".pdf,.txt,application/pdf,text/plain"
              onChange={(e) => { setArchivo(e.target.files?.[0] ?? null); if (error) setError(null) }}
              className="w-full text-sm text-gray-700 file:mr-3 file:rounded-lg file:border-0
                         file:bg-blue-50 file:px-4 file:py-2 file:text-blue-700 hover:file:bg-blue-100"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              {archivo
                ? `${archivo.name} · ${(archivo.size / 1024).toFixed(0)} KB`
                : 'El sistema extraerá el texto y descartará el archivo; no se guarda.'}
            </p>
          </div>
        ) : (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              URL de la política de privacidad
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => { setUrl(e.target.value); if (error) setError(null) }}
              placeholder="https://ejemplo.com/politica-de-privacidad"
              className="w-full border border-gray-300 rounded-lg p-3 text-sm
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              El sistema descargará y extraerá automáticamente el texto.
            </p>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {loading && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-700">{mensajeCarga}</p>
          </div>
        )}

        <Button
          type="submit"
          isLoading={loading}
          disabled={pestana === 'texto' && (chars < MIN_CHARS || chars > MAX_CHARS)}
          className="w-full"
        >
          Analizar política
        </Button>
      </form>
    </div>
  )
}
