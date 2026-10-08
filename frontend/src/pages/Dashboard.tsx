import { Link } from 'react-router-dom'
import { ArrowRight, BookOpen, History, ShieldPlus } from 'lucide-react'
import PanelEstadistico from '@/components/dashboard/PanelEstadistico'
import { useAuth } from '@/hooks/useAuth'

const ACCESO =
  'flex items-center gap-4 rounded-2xl border border-borde bg-superficie p-4 transition-colors hover:border-marca-borde'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <main className="mx-auto max-w-5xl px-4 py-6 pb-16">
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold tracking-tight text-texto sm:text-3xl">
          Bienvenido{user ? `, ${user.nombre}` : ''}
        </h1>
        <p className="mt-1 text-base text-texto-2">
          Analiza políticas de privacidad y entiende cómo se usan tus datos personales.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
        <div className="space-y-3">
          <Link
            to="/analizar"
            className="flex items-center gap-4 rounded-2xl bg-marca p-5 text-white transition-colors hover:bg-marca-hover"
          >
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/15">
              <ShieldPlus size={26} aria-hidden="true" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-lg font-bold">Analizar política</span>
              <span className="block text-sm text-white/90">Pega el texto, ingresa una URL o carga un archivo</span>
            </span>
            <ArrowRight size={22} aria-hidden="true" className="shrink-0" />
          </Link>

          <Link to="/historial" className={ACCESO}>
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-marca-suave text-marca-texto">
              <History size={24} aria-hidden="true" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block font-bold text-texto">Mis análisis</span>
              <span className="block text-sm text-texto-2">Consulta tu historial de análisis</span>
            </span>
          </Link>

          <Link to="/glosario" className={ACCESO}>
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-marca-suave text-marca-texto">
              <BookOpen size={24} aria-hidden="true" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block font-bold text-texto">Glosario</span>
              <span className="block text-sm text-texto-2">Términos de privacidad explicados de forma sencilla</span>
            </span>
          </Link>
        </div>

        <PanelEstadistico />
      </div>
    </main>
  )
}
