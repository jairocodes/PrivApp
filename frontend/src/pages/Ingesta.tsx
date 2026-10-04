import IngestaForm from '@/components/ingesta/IngestaForm'

export default function Ingesta() {
  return (
    <>
      <main className="max-w-2xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-texto mb-2">Analizar política</h1>
        <p className="text-texto-2 mb-6">
          Pega el texto de una política de privacidad o ingresa su URL.
        </p>
        <IngestaForm />
      </main>
    </>
  )
}
