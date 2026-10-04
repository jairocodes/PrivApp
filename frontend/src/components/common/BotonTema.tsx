import { Moon, Sun } from 'lucide-react'
import { useTema } from '@/hooks/useTema'

/** Interruptor del modo oscuro: icono de sol en oscuro y de luna en claro. */
export default function BotonTema() {
  const { oscuro, alternar } = useTema()

  return (
    <button
      type="button"
      onClick={alternar}
      aria-pressed={oscuro}
      aria-label="Modo oscuro"
      className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-borde-fuerte bg-superficie text-texto transition-colors hover:bg-superficie-2"
    >
      {oscuro ? <Sun size={20} aria-hidden="true" /> : <Moon size={20} aria-hidden="true" />}
    </button>
  )
}
