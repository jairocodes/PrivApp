import { useState } from 'react'
import { analisisApi } from '@/api/analisis'
import type { AnalisisResult } from '@/types/analisis'

export function useAnalisis() {
  const [resultado, setResultado] = useState<AnalisisResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const iniciar = async (texto: string): Promise<AnalisisResult | null> => {
    setIsLoading(true)
    setError(null)
    setResultado(null)
    try {
      const res = await analisisApi.iniciar(texto)
      setResultado(res.data)
      return res.data
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        'No fue posible completar el análisis. Intenta nuevamente.'
      setError(msg)
      return null
    } finally {
      setIsLoading(false)
    }
  }

  const obtener = async (id: string | number): Promise<void> => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await analisisApi.obtener(id)
      setResultado(res.data)
    } catch {
      setError('No fue posible cargar el análisis.')
    } finally {
      setIsLoading(false)
    }
  }

  return { resultado, isLoading, error, iniciar, obtener }
}
