import type { ResumenGeneral, SeccionAnalizada } from '@/types/analisis'
import {
  contarPorNivel,
  explicarNivel,
  hallazgosQueCuentan,
  hallazgosSinRespaldo,
} from '@/utils/resumenResultados'

interface Props {
  resumen: ResumenGeneral
  secciones: SeccionAnalizada[]
}

const BARRAS = [
  { nivel: 'alto', etiqueta: 'Riesgo alto', texto: 'text-riesgo-alto', barra: 'bg-riesgo-alto-solido' },
  { nivel: 'medio', etiqueta: 'Riesgo medio', texto: 'text-riesgo-medio', barra: 'bg-riesgo-medio-solido' },
  { nivel: 'bajo', etiqueta: 'Buenas prácticas', texto: 'text-riesgo-bajo', barra: 'bg-riesgo-bajo-solido' },
] as const

/** Qué hallazgos explican la puntuación y el nivel (como los factores de un
 *  puntaje de crédito): lo que cuenta y la regla que decide el nivel. */
export default function PorQueResultado({ resumen, secciones }: Props) {
  const cuentan = hallazgosQueCuentan(secciones)
  const conteo = contarPorNivel(cuentan)
  const sinRespaldo = hallazgosSinRespaldo(secciones)
  const total = cuentan.length

  return (
    <section aria-labelledby="titulo-por-que" className="card space-y-4">
      <div className="space-y-1">
        <h2 id="titulo-por-que" className="text-lg font-bold text-texto">
          ¿Por qué este resultado?
        </h2>
        <p className="text-sm text-texto-2">
          Revisamos {secciones.length} {secciones.length === 1 ? 'sección' : 'secciones'} y encontramos {total}{' '}
          {total === 1 ? 'cláusula que cuenta' : 'cláusulas que cuentan'} para el resultado.
        </p>
      </div>

      <ul className="space-y-3">
        {BARRAS.map(({ nivel, etiqueta, texto, barra }) => (
          <li key={nivel} className="space-y-1.5">
            <div className="flex justify-between text-sm">
              <span className={`font-semibold ${texto}`}>{etiqueta}</span>
              <span className="font-bold text-texto">{conteo[nivel]}</span>
            </div>
            <div aria-hidden="true" className="h-2.5 rounded-full bg-superficie-2">
              <div
                className={`h-2.5 rounded-full ${barra}`}
                style={{ width: total ? `${(conteo[nivel] / total) * 100}%` : '0%' }}
              />
            </div>
          </li>
        ))}
      </ul>

      <p className="rounded-xl bg-superficie-2 px-4 py-3 text-sm text-texto">{explicarNivel(resumen, conteo)}</p>
      {sinRespaldo > 0 && (
        <p className="text-xs text-texto-2">
          {sinRespaldo === 1
            ? '1 hallazgo sin respaldo en el corpus normativo se muestra, pero no cuenta.'
            : `${sinRespaldo} hallazgos sin respaldo en el corpus normativo se muestran, pero no cuentan.`}
        </p>
      )}
    </section>
  )
}
