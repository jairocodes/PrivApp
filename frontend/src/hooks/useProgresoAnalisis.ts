import { useEffect, useState } from 'react'
import { analisisApi } from '@/api/analisis'
import type { EstadoAnalisis } from '@/types/analisis'

const INTERVALO_POLLING_MS = 1500

export function useProgresoAnalisis(id: string | undefined) {
  const [estado, setEstado] = useState<EstadoAnalisis>('procesando')
  const [seccionActual, setSeccionActual] = useState(0)
  const [seccionesTotal, setSeccionesTotal] = useState<number | null>(null)

  useEffect(() => {
    if (!id) return

    let activo = true
    let intervalo: ReturnType<typeof setInterval>

    const consultar = async () => {
      try {
        const { data } = await analisisApi.consultarEstado(id)
        if (!activo) return
        setEstado(data.estado)
        setSeccionActual(data.seccion_actual)
        setSeccionesTotal(data.secciones_total)
        if (data.estado !== 'procesando') {
          clearInterval(intervalo)
        }
      } catch {
        if (activo) {
          setEstado('error')
          clearInterval(intervalo)
        }
      }
    }

    consultar()
    intervalo = setInterval(consultar, INTERVALO_POLLING_MS)

    return () => {
      activo = false
      clearInterval(intervalo)
    }
  }, [id])

  return { estado, seccionActual, seccionesTotal }
}
