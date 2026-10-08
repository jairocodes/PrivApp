import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DistribucionNiveles } from '@/types/analisis'

// Colores del tema (modo claro y oscuro): recharts escribe el color como
// atributo del SVG, y una clase de CSS tiene prioridad sobre él.
const CLASE_NIVEL = {
  bajo: 'fill-riesgo-bajo-solido',
  medio: 'fill-riesgo-medio-solido',
  alto: 'fill-riesgo-alto-solido',
} as const

interface Props {
  distribucion: DistribucionNiveles
}

export default function GraficoDistribucion({ distribucion }: Props) {
  const datos = (['bajo', 'medio', 'alto'] as const).map((nivel) => ({
    nivel,
    etiqueta: nivel.charAt(0).toUpperCase() + nivel.slice(1),
    cantidad: distribucion[nivel],
  }))
  const resumen = datos.map((d) => `${d.cantidad} de riesgo ${d.nivel}`).join(', ')

  return (
    // Los ejes toman el color del texto (currentColor).
    <div role="img" aria-label={`Distribución por nivel de riesgo: ${resumen}`} className="h-44 w-full text-texto-2">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={datos} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <XAxis dataKey="etiqueta" tickLine={false} axisLine={false} fontSize={12} tick={{ fill: 'currentColor' }} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} tick={{ fill: 'currentColor' }} />
          <Tooltip
            cursor={{ fill: 'currentColor', opacity: 0.08 }}
            contentStyle={{
              backgroundColor: 'rgb(var(--superficie))',
              borderColor: 'rgb(var(--borde))',
              borderRadius: 12,
              color: 'rgb(var(--texto))',
            }}
            formatter={(valor) => [valor, 'Análisis']}
          />
          <Bar dataKey="cantidad" radius={[6, 6, 0, 0]}>
            {datos.map((d) => (
              <Cell key={d.nivel} className={CLASE_NIVEL[d.nivel]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
