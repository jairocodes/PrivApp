import { Monitor, Moon, Sun } from 'lucide-react'
import type { PreferenciaTema } from '@/context/TemaContext'
import { useTema } from '@/hooks/useTema'

const OPCIONES: { valor: PreferenciaTema; etiqueta: string; icono: typeof Sun }[] = [
  { valor: 'claro', etiqueta: 'Claro', icono: Sun },
  { valor: 'oscuro', etiqueta: 'Oscuro', icono: Moon },
  { valor: 'sistema', etiqueta: 'Automático', icono: Monitor },
]

/** Elección del tema: claro, oscuro o el del dispositivo. Se recuerda en este navegador. */
export default function Apariencia() {
  const { preferencia, cambiarPreferencia } = useTema()

  return (
    <fieldset className="card space-y-3">
      <legend className="float-left mb-3 w-full text-lg font-bold text-texto">Apariencia</legend>
      <p className="clear-left text-sm text-texto-2">
        "Automático" usa el modo del teléfono o la computadora. Se recuerda en este navegador.
      </p>
      <div className="grid grid-cols-3 gap-2">
        {OPCIONES.map(({ valor, etiqueta, icono: Icono }) => {
          const elegida = preferencia === valor
          return (
            <label
              key={valor}
              className={`flex min-h-[72px] cursor-pointer flex-col items-center justify-center gap-1.5 rounded-2xl border-2 px-2 py-3 text-sm font-bold transition-colors focus-within:ring-2 focus-within:ring-marca ${
                elegida ? 'border-marca bg-marca-suave text-marca-suave-texto' : 'border-borde text-texto-2 hover:border-borde-fuerte'
              }`}
            >
              <input
                type="radio"
                name="tema"
                value={valor}
                checked={elegida}
                onChange={() => cambiarPreferencia(valor)}
                className="sr-only"
              />
              <Icono size={22} aria-hidden="true" />
              {etiqueta}
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}
