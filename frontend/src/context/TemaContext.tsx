import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

export type PreferenciaTema = 'claro' | 'oscuro' | 'sistema'

export interface TemaContextValue {
  /** Lo que eligió la persona; 'sistema' sigue la configuración del dispositivo. */
  preferencia: PreferenciaTema
  /** true si en este momento se muestra el modo oscuro. */
  oscuro: boolean
  cambiarPreferencia: (preferencia: PreferenciaTema) => void
  /** Pasa al modo contrario del que se ve ahora y lo recuerda. */
  alternar: () => void
}

// La misma clave y los mismos valores los lee el script de index.html, que
// aplica el tema antes del primer pintado.
export const CLAVE_TEMA = 'privapp-tema'
const CONSULTA_OSCURO = '(prefers-color-scheme: dark)'

export const TemaContext = createContext<TemaContextValue | null>(null)

function leerPreferencia(): PreferenciaTema {
  try {
    const valor = localStorage.getItem(CLAVE_TEMA)
    return valor === 'claro' || valor === 'oscuro' ? valor : 'sistema'
  } catch {
    return 'sistema'
  }
}

function guardarPreferencia(preferencia: PreferenciaTema) {
  try {
    if (preferencia === 'sistema') localStorage.removeItem(CLAVE_TEMA)
    else localStorage.setItem(CLAVE_TEMA, preferencia)
  } catch {
    // Almacenamiento bloqueado (navegación privada): el tema dura solo esta visita.
  }
}

function sistemaEnOscuro(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia(CONSULTA_OSCURO).matches
}

export function TemaProvider({ children }: { children: ReactNode }) {
  const [preferencia, setPreferencia] = useState<PreferenciaTema>(leerPreferencia)
  const [sistemaOscuro, setSistemaOscuro] = useState(sistemaEnOscuro)

  // Sigue los cambios del dispositivo (p. ej. el modo oscuro automático de noche).
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return
    const consulta = window.matchMedia(CONSULTA_OSCURO)
    const alCambiar = (evento: MediaQueryListEvent) => setSistemaOscuro(evento.matches)
    consulta.addEventListener('change', alCambiar)
    return () => consulta.removeEventListener('change', alCambiar)
  }, [])

  const oscuro = preferencia === 'oscuro' || (preferencia === 'sistema' && sistemaOscuro)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', oscuro)
  }, [oscuro])

  const cambiarPreferencia = useCallback((nueva: PreferenciaTema) => {
    guardarPreferencia(nueva)
    setPreferencia(nueva)
  }, [])

  const alternar = useCallback(() => {
    cambiarPreferencia(oscuro ? 'claro' : 'oscuro')
  }, [oscuro, cambiarPreferencia])

  const valor = useMemo(
    () => ({ preferencia, oscuro, cambiarPreferencia, alternar }),
    [preferencia, oscuro, cambiarPreferencia, alternar],
  )

  return <TemaContext.Provider value={valor}>{children}</TemaContext.Provider>
}
