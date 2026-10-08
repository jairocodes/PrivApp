import { CONFIG } from '@/components/analisis/IndicadorSemaforo'
import type { NivelRiesgo } from '@/types/analisis'

interface Props {
  puntaje: number
  nivel: NivelRiesgo
}

// Semicírculo de 0 (izquierda) a 100 (derecha), con las franjas de la RN-05:
// la puntuación es baja por debajo de 25, media hasta 75 y alta desde 75.
const CENTRO = { x: 130, y: 130 }
const RADIO = 110
// La aguja va del borde de la zona de la cifra hasta el arco: nunca cruza los números,
// que ocupan el centro (hasta ~70 px del eje, incluso con «100/100»).
export const AGUJA = { desde: 76, hasta: 98 }
const FRANJAS = [
  { desde: 0, hasta: 25, clase: 'stroke-riesgo-bajo-solido' },
  { desde: 25, hasta: 75, clase: 'stroke-riesgo-medio-solido' },
  { desde: 75, hasta: 100, clase: 'stroke-riesgo-alto-solido' },
]

function punto(valor: number, radio: number) {
  const angulo = ((180 - valor * 1.8) * Math.PI) / 180
  return { x: CENTRO.x + radio * Math.cos(angulo), y: CENTRO.y - radio * Math.sin(angulo) }
}

function arco(desde: number, hasta: number) {
  const inicio = punto(desde, RADIO)
  const fin = punto(hasta, RADIO)
  return `M${inicio.x.toFixed(1)} ${inicio.y.toFixed(1)} A${RADIO} ${RADIO} 0 0 1 ${fin.x.toFixed(1)} ${fin.y.toFixed(1)}`
}

/** Puntuación de riesgo (0–100) con las franjas de referencia, para que el
 *  número tenga contexto. El nombre accesible dice la puntuación y el nivel. */
export default function MedidorRiesgo({ puntaje, nivel }: Props) {
  const valor = Math.min(100, Math.max(0, puntaje))
  const inicio = punto(valor, AGUJA.desde)
  const fin = punto(valor, AGUJA.hasta)

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        role="img"
        aria-label={`Puntuación de riesgo: ${puntaje} de 100, ${CONFIG[nivel].label}`}
        className="relative h-[150px] w-[260px]"
      >
        <svg width="260" height="150" viewBox="0 0 260 150" aria-hidden="true">
          {FRANJAS.map((franja) => (
            <path
              key={franja.desde}
              d={arco(franja.desde, franja.hasta)}
              fill="none"
              strokeWidth="22"
              className={`${franja.clase} opacity-50`}
            />
          ))}
          <line
            x1={inicio.x.toFixed(1)}
            y1={inicio.y.toFixed(1)}
            x2={fin.x.toFixed(1)}
            y2={fin.y.toFixed(1)}
            strokeWidth="5"
            strokeLinecap="round"
            className="stroke-texto"
          />
        </svg>
        <div aria-hidden="true" className="absolute inset-x-0 -bottom-1 flex items-baseline justify-center gap-0.5">
          <span className="text-5xl font-extrabold tracking-tight text-texto">{puntaje}</span>
          <span className="text-base font-semibold text-texto-2">/100</span>
        </div>
      </div>
      <div aria-hidden="true" className="flex w-[260px] justify-between text-xs text-texto-2">
        <span>0 · Bajo</span>
        <span>Medio</span>
        <span>Alto · 100</span>
      </div>
    </div>
  )
}
