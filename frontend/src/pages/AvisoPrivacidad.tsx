import Navbar from '@/components/common/Navbar'

// El texto del aviso lo proporciona el responsable del proyecto.
export const CONTENIDO_AVISO = 'PENDIENTE_CONTENIDO'

export default function AvisoPrivacidad() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Aviso de privacidad de PrivApp</h1>
        <article className="card text-sm text-gray-700 leading-relaxed whitespace-pre-line">
          {CONTENIDO_AVISO}
        </article>
      </main>
    </div>
  )
}
