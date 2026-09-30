import Button from '@/components/common/Button'
import type { IngestaResponse } from '@/types/ingesta'

interface Props {
  resultado: IngestaResponse
  iniciando?: boolean
  error?: string | null
  onConfirmar: () => void
  onCorregir: () => void
  onCancelar: () => void
}

function describirFuente(fuente: string): string {
  if (fuente === 'texto_directo') return 'Texto pegado'
  if (/^https?:\/\//i.test(fuente)) return `Dirección web: ${fuente}`
  return `Archivo: ${fuente}`
}

export default function VistaPreviaTexto({
  resultado,
  iniciando = false,
  error = null,
  onConfirmar,
  onCorregir,
  onCancelar,
}: Props) {
  return (
    <section aria-labelledby="titulo-vista-previa" className="space-y-4">
      <div>
        <h3 id="titulo-vista-previa" className="text-lg font-semibold text-gray-800">
          Revisa el texto antes de analizarlo
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          Confirma que corresponde a la política que quieres evaluar.
        </p>
      </div>

      <dl className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <div className="flex gap-1">
          <dt className="text-gray-500">Origen:</dt>
          <dd className="text-gray-800 break-all">{describirFuente(resultado.fuente)}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="text-gray-500">Caracteres:</dt>
          <dd className="text-gray-800">{resultado.caracteres.toLocaleString('es-GT')}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="text-gray-500">Palabras:</dt>
          <dd className="text-gray-800">{resultado.palabras.toLocaleString('es-GT')}</dd>
        </div>
      </dl>

      <div
        tabIndex={0}
        aria-label="Texto que se analizará"
        className="max-h-80 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-3
                   text-sm text-gray-700 leading-relaxed whitespace-pre-wrap"
      >
        {resultado.texto_procesado}
      </div>

      {error && (
        <div role="alert" className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={onConfirmar} isLoading={iniciando}>
          Confirmar y analizar
        </Button>
        <Button type="button" variant="secondary" onClick={onCorregir} disabled={iniciando}>
          Corregir
        </Button>
        <Button type="button" variant="secondary" onClick={onCancelar} disabled={iniciando}>
          Cancelar
        </Button>
      </div>
    </section>
  )
}
