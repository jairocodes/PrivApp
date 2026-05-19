import Navbar from '@/components/common/Navbar'
import IngestaForm from '@/components/ingesta/IngestaForm'

export default function Ingesta() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Analizar política</h1>
        <p className="text-gray-600 mb-6">
          Pega el texto de una política de privacidad o ingresa su URL.
        </p>
        <IngestaForm />
      </main>
    </div>
  )
}
