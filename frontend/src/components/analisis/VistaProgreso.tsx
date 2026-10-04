import { useEffect, useState } from 'react'
import { Lightbulb } from 'lucide-react'
import { Spinner } from '@/components/common/Cargando'
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
      <Spinner etiqueta="Analizando" className="mx-auto h-14 w-14" />

      <div>
        <p className="text-texto-2 font-medium">
          {seccionesTotal
            ? `Analizando la política: ${seccionActual} de ${seccionesTotal} secciones listas...`
            : 'Preparando el análisis...'}
        </p>
        {progreso !== null && (
          <div className="w-full max-w-xs mx-auto mt-3 h-2 rounded-full bg-superficie-2 overflow-hidden">
            <div
              className="h-full bg-marca transition-all duration-500"
              style={{ width: `${progreso}%` }}
            />
          </div>
        )}
      </div>

      <div className="max-w-sm mx-auto rounded-xl border border-marca-borde bg-marca-suave p-4 text-left">
        <div className="flex items-center gap-2 mb-1">
          <Lightbulb size={14} className="text-marca-texto" />
          <p className="text-xs font-semibold text-marca-texto uppercase tracking-wide">
            Consejo de privacidad
          </p>
        </div>
        <p className="text-sm text-marca-suave-texto leading-relaxed">
          {CONSEJOS_PRIVACIDAD[indiceConsejo]}
        </p>
      </div>
    </div>
  )
}
