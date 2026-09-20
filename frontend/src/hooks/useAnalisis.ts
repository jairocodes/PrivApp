import { useState } from 'react'
import { analisisApi } from '@/api/analisis'
import type { AnalisisResult } from '@/types/analisis'

export function useAnalisis() {
  const [resultado, setResultado] = useState<AnalisisResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  return { resultado, isLoading, error, obtener }
}
