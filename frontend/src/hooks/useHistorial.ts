import { useState } from 'react'
import { analisisApi } from '@/api/analisis'
import type { AnalisisHistorialItem, FiltrosHistorial } from '@/types/analisis'

export function useHistorial() {
  const [items, setItems] = useState<AnalisisHistorialItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [filtros, setFiltros] = useState<FiltrosHistorial>({})
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Sin filtros explícitos se conservan los vigentes (p. ej. al cambiar de página).
  const cargar = async (paginaSolicitada = 1, nuevosFiltros: FiltrosHistorial = filtros): Promise<void> => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await analisisApi.listar(paginaSolicitada, pageSize, nuevosFiltros)
      setItems(res.data.items)
      setTotal(res.data.total)
      setPage(res.data.page)
      setFiltros(nuevosFiltros)
    } catch {
      setError('No fue posible cargar el historial de análisis.')
    } finally {
      setIsLoading(false)
    }
  }

  return { items, total, page, pageSize, filtros, isLoading, error, cargar }
}
