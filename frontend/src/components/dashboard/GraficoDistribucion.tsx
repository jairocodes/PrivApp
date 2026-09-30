import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DistribucionNiveles } from '@/types/analisis'

// Mismos colores que la paleta riesgo.* de tailwind.config.js.
const COLOR_NIVEL = { bajo: '#22c55e', medio: '#f59e0b', alto: '#ef4444' } as const

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
    <div role="img" aria-label={`Distribución por nivel de riesgo: ${resumen}`} className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={datos} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <XAxis dataKey="etiqueta" tickLine={false} axisLine={false} fontSize={12} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} />
          <Tooltip cursor={{ fill: 'rgba(0,0,0,0.04)' }} formatter={(valor) => [valor, 'Análisis']} />
          <Bar dataKey="cantidad" radius={[6, 6, 0, 0]}>
            {datos.map((d) => (
              <Cell key={d.nivel} fill={COLOR_NIVEL[d.nivel]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
