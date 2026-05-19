import { Link } from 'react-router-dom'
import { FileSearch, ShieldCheck } from 'lucide-react'
import Navbar from '@/components/common/Navbar'
import { useAuth } from '@/hooks/useAuth'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Bienvenido{user ? `, ${user.nombre}` : ''}
        </h1>
        <p className="text-gray-600 mb-8">
          Analiza políticas de privacidad y entiende cómo se usan tus datos personales.
        </p>

        <div className="grid gap-4 sm:grid-cols-2">
          <Link
            to="/analizar"
            className="card flex items-center gap-4 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
          >
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileSearch size={24} className="text-blue-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">Analizar política</h2>
              <p className="text-sm text-gray-500">Pega el texto o ingresa una URL</p>
            </div>
          </Link>

          <div className="card flex items-center gap-4 opacity-50 cursor-not-allowed">
            <div className="p-3 bg-gray-100 rounded-lg">
              <ShieldCheck size={24} className="text-gray-400" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">Mis análisis</h2>
              <p className="text-sm text-gray-500">Disponible en versión final</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
