import EncabezadoPagina from '@/components/common/EncabezadoPagina'
import IngestaForm from '@/components/ingesta/IngestaForm'

export default function Ingesta() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-6 pb-16">
      <EncabezadoPagina
        titulo="Analiza una política"
        subtitulo="Pega el texto, el enlace o el archivo de una política de privacidad y te decimos qué hace la app con tus datos."
      />
      <IngestaForm />
    </main>
  )
}
