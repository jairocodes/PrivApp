import { useState } from 'react'
import Button from '@/components/common/Button'
import type { DeteccionPolitica, IngestaResponse } from '@/types/ingesta'
import Aviso from '@/components/common/Aviso'
import { Casilla } from '@/components/common/Campos'

interface Props {
  resultado: IngestaResponse
  iniciando?: boolean
  error?: string | null
  onConfirmar: () => void
  onCorregir: () => void
  onCancelar: () => void
}

// Nombres legibles de los temas que devuelve la detección (sin tildes en el servidor).
const NOMBRE_TEMA: Record<string, string> = {
  conservacion: 'conservación de los datos',
  cambios: 'cambios en la política',
  contacto: 'contacto del responsable',
}

function describirFuente(fuente: string): string {
  if (fuente === 'texto_directo') return 'Texto pegado'
  if (/^https?:\/\//i.test(fuente)) return `Dirección web: ${fuente}`
  return `Archivo: ${fuente}`
}

function AvisoDudosa({ deteccion }: { deteccion: DeteccionPolitica }) {
  const temas = deteccion.temas_encontrados.map((tema) => NOMBRE_TEMA[tema] ?? tema)
  return (
    <Aviso tipo="info">
      <p className="font-semibold">Este texto no parece una política de privacidad típica.</p>
      <p className="mt-1">
        Encontramos {deteccion.temas_encontrados.length} de {deteccion.temas_total} temas habituales
        {temas.length > 0 ? ` (${temas.join(', ')})` : ''}, pero no queda claro que explique cómo una app o
        un sitio usa tus datos. Si es una política de privacidad, confírmalo para analizarla.
      </p>
    </Aviso>
  )
}

export default function VistaPreviaTexto({
  resultado,
  iniciando = false,
  error = null,
  onConfirmar,
  onCorregir,
  onCancelar,
}: Props) {
  const dudosa = resultado.deteccion?.resultado === 'dudosa'
  const [confirmada, setConfirmada] = useState(false)

  return (
    <section aria-labelledby="titulo-vista-previa" className="space-y-4">
      <div>
        <h3 id="titulo-vista-previa" className="text-lg font-semibold text-texto">
          Revisa el texto antes de analizarlo
        </h3>
        <p className="text-sm text-texto-2 mt-1">
          Confirma que corresponde a la política que quieres evaluar.
        </p>
      </div>

      <dl className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <div className="flex gap-1">
          <dt className="text-texto-2">Origen:</dt>
          <dd className="text-texto break-all">{describirFuente(resultado.fuente)}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="text-texto-2">Caracteres:</dt>
          <dd className="text-texto">{resultado.caracteres.toLocaleString('es-GT')}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="text-texto-2">Palabras:</dt>
          <dd className="text-texto">{resultado.palabras.toLocaleString('es-GT')}</dd>
        </div>
      </dl>

      {dudosa && resultado.deteccion && <AvisoDudosa deteccion={resultado.deteccion} />}

      <div
        tabIndex={0}
        aria-label="Texto que se analizará"
        className="max-h-80 overflow-y-auto rounded-lg border border-borde bg-superficie-2 p-3
                   text-sm text-texto-2 leading-relaxed whitespace-pre-wrap"
      >
        {resultado.texto_procesado}
      </div>

      {dudosa && (
        <Casilla checked={confirmada} onChange={(e) => setConfirmada(e.target.checked)} disabled={iniciando}>
          Confirmo que este texto es una política de privacidad o explica cómo se usan los datos personales.
        </Casilla>
      )}

      {error && (
        <Aviso tipo="error">{error}</Aviso>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={onConfirmar} isLoading={iniciando} disabled={dudosa && !confirmada}>
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
