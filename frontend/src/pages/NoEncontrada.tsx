import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'

/** Cualquier dirección que no existe: explica qué pasó y ofrece por dónde seguir. */
export default function NoEncontrada() {
  return (
    <main className="mx-auto flex max-w-md flex-col items-center px-4 py-16 text-center">
      <span className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-marca-suave text-marca-texto">
        <Compass size={32} aria-hidden="true" />
      </span>
      <h1 className="text-2xl font-extrabold text-texto">Página no encontrada</h1>
      <p className="mt-2 text-base text-texto-2">
        La dirección que abriste no existe o ya no está disponible.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        <Link to="/dashboard" className="btn-primary">
          Ir al inicio
        </Link>
        <Link to="/glosario" className="btn-secondary">
          Ver el glosario
        </Link>
      </div>
    </main>
  )
}
