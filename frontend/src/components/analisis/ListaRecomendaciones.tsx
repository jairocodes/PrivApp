import { Lightbulb } from 'lucide-react'
import AyudaGlosario from '@/components/glosario/AyudaGlosario'

interface Props {
  recomendaciones: string[]
}

export default function ListaRecomendaciones({ recomendaciones }: Props) {
  if (recomendaciones.length === 0) return null

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb size={20} className="text-yellow-500" />
        <h2 className="text-lg font-semibold text-gray-800">Recomendaciones</h2>
        <AyudaGlosario termino="Recomendación" />
      </div>
      <ul className="space-y-3">
        {recomendaciones.map((rec, i) => (
          <li key={i} className="flex items-start gap-3 text-sm text-gray-700 leading-relaxed">
            <span className="shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-700
                             flex items-center justify-center text-xs font-bold mt-0.5">
              {i + 1}
            </span>
            {rec}
          </li>
        ))}
      </ul>
    </div>
  )
}
