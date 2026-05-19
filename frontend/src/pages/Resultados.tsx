import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import Navbar from '@/components/common/Navbar'
import { useAnalisis } from '@/hooks/useAnalisis'

export default function Resultados() {
  const { id } = useParams<{ id: string }>()
  const { resultado, isLoading, error, obtener } = useAnalisis()

  useEffect(() => {
    if (id) obtener(id)
  }, [id])

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Resultados del análisis</h1>

        {isLoading && <p className="text-gray-500">Analizando política...</p>}
        {error && <p className="text-red-600">{error}</p>}
        {resultado && (
          <p className="text-gray-500 text-sm">
            Panel de visualización — implementación completa en Sprint 5.
          </p>
        )}
      </main>
    </div>
  )
}
