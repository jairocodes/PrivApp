import { ShieldCheck } from 'lucide-react'

interface Props {
  titulo: string
  subtitulo: string
}

/** Encabezado de las pantallas de acceso: marca, título y para qué sirve PrivApp. */
export default function Bienvenida({ titulo, subtitulo }: Props) {
  return (
    <div className="mb-6 flex flex-col items-center gap-3 text-center">
      <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-marca text-white shadow-sm">
        <ShieldCheck size={36} aria-hidden="true" />
      </span>
      <h1 className="text-3xl font-extrabold tracking-tight text-texto">{titulo}</h1>
      <p className="max-w-xs text-base text-texto-2">{subtitulo}</p>
    </div>
  )
}
