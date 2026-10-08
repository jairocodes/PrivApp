import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="border-t border-borde bg-superficie px-4 py-4">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 text-sm text-texto-2">
        <span className="font-semibold">PrivApp</span>
        <nav aria-label="Enlaces del pie de página" className="flex items-center gap-2">
          <Link to="/glosario" className="inline-flex min-h-[44px] items-center px-2 hover:text-marca-texto hover:underline">
            Glosario
          </Link>
          <Link to="/aviso-privacidad" className="inline-flex min-h-[44px] items-center px-2 hover:text-marca-texto hover:underline">
            Aviso de privacidad
          </Link>
        </nav>
      </div>
    </footer>
  )
}
