import { useEffect, useState } from 'react'
import { Lightbulb } from 'lucide-react'
import { CONSEJOS_PRIVACIDAD } from '@/data/consejosPrivacidad'

interface Props {
  seccionActual: number
  seccionesTotal: number | null
}

const ROTACION_CONSEJO_MS = 6000

export default function VistaProgreso({ seccionActual, seccionesTotal }: Props) {
  const [indiceConsejo, setIndiceConsejo] = useState(0)

  useEffect(() => {
    const intervalo = setInterval(() => {
      setIndiceConsejo((i) => (i + 1) % CONSEJOS_PRIVACIDAD.length)
    }, ROTACION_CONSEJO_MS)
    return () => clearInterval(intervalo)
  }, [])

  const progreso =
    seccionesTotal && seccionesTotal > 0
      ? Math.min(100, Math.round((seccionActual / seccionesTotal) * 100))
      : null

  return (
    <div className="card text-center py-12 space-y-6">
      <div
        className="inline-flex w-14 h-14 rounded-full border-4 border-blue-200 border-t-blue-600
                   animate-spin mx-auto"
        role="status"
        aria-label="Analizando"
      />

      <div>
        <p className="text-gray-700 font-medium">
          {seccionesTotal
            ? `Analizando la política: ${seccionActual} de ${seccionesTotal} secciones listas...`
            : 'Preparando el análisis...'}
        </p>
        {progreso !== null && (
          <div className="w-full max-w-xs mx-auto mt-3 h-2 rounded-full bg-gray-100 overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-500"
              style={{ width: `${progreso}%` }}
            />
          </div>
        )}
      </div>

      <div className="max-w-sm mx-auto rounded-xl border border-blue-100 bg-blue-50 p-4 text-left">
        <div className="flex items-center gap-2 mb-1">
          <Lightbulb size={14} className="text-blue-500" />
          <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
            Consejo de privacidad
          </p>
        </div>
        <p className="text-sm text-blue-800 leading-relaxed">
          {CONSEJOS_PRIVACIDAD[indiceConsejo]}
        </p>
      </div>
    </div>
  )
}
