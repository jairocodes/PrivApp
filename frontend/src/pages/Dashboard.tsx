import { Link } from 'react-router-dom'
import { FileSearch, ShieldCheck } from 'lucide-react'
import PanelEstadistico from '@/components/dashboard/PanelEstadistico'
import { useAuth } from '@/hooks/useAuth'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <>
      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-texto mb-2">
          Bienvenido{user ? `, ${user.nombre}` : ''}
        </h1>
        <p className="text-texto-2 mb-8">
          Analiza políticas de privacidad y entiende cómo se usan tus datos personales.
        </p>

        <div className="grid gap-4 sm:grid-cols-2">
          <Link
            to="/analizar"
            className="card flex items-center gap-4 hover:border-marca-borde hover:shadow-md transition-all cursor-pointer"
          >
            <div className="p-3 bg-marca-suave rounded-lg">
              <FileSearch size={24} className="text-marca-texto" />
            </div>
            <div>
              <h2 className="font-semibold text-texto">Analizar política</h2>
              <p className="text-sm text-texto-2">Pega el texto, ingresa una URL o carga un archivo</p>
            </div>
          </Link>

          <Link
            to="/historial"
            className="card flex items-center gap-4 hover:border-marca-borde hover:shadow-md transition-all cursor-pointer"
          >
            <div className="p-3 bg-marca-suave rounded-lg">
              <ShieldCheck size={24} className="text-marca-texto" />
            </div>
            <div>
              <h2 className="font-semibold text-texto">Mis análisis</h2>
              <p className="text-sm text-texto-2">Consulta tu historial de análisis</p>
            </div>
          </Link>
        </div>

        <div className="mt-6">
          <PanelEstadistico />
        </div>
      </main>
    </>
  )
}
