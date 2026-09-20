import { useState } from 'react'
import { analisisApi } from '@/api/analisis'
import type { AnalisisHistorialItem } from '@/types/analisis'

export function useHistorial() {
  const [items, setItems] = useState<AnalisisHistorialItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cargar = async (paginaSolicitada = 1): Promise<void> => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await analisisApi.listar(paginaSolicitada, pageSize)
      setItems(res.data.items)
      setTotal(res.data.total)
      setPage(res.data.page)
    } catch {
      setError('No fue posible cargar el historial de análisis.')
    } finally {
      setIsLoading(false)
    }
  }

  return { items, total, page, pageSize, isLoading, error, cargar }
}
