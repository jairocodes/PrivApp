import { useState } from 'react'
import { adminApi } from '@/api/admin'
import type { UsuarioAdmin } from '@/types/admin'

export function useUsuariosAdmin() {
  const [items, setItems] = useState<UsuarioAdmin[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [busqueda, setBusqueda] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cargar = async (paginaSolicitada = 1, texto = busqueda): Promise<void> => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await adminApi.listarUsuarios(paginaSolicitada, pageSize, texto)
      setItems(res.data.items)
      setTotal(res.data.total)
      setPage(res.data.page)
      setBusqueda(texto)
    } catch {
      setError('No fue posible cargar el listado de usuarios.')
    } finally {
      setIsLoading(false)
    }
  }

  const reemplazar = (actualizado: UsuarioAdmin) => {
    setItems((actuales) => actuales.map((u) => (u.id === actualizado.id ? actualizado : u)))
  }

  return { items, total, page, pageSize, busqueda, isLoading, error, cargar, reemplazar }
}
