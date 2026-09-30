import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 px-4 py-4">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-3 text-xs text-gray-500">
        <span>PrivApp</span>
        <nav aria-label="Enlaces del pie de página" className="flex items-center gap-4">
          <Link to="/glosario" className="hover:text-blue-600 hover:underline">
            Glosario
          </Link>
          <Link to="/aviso-privacidad" className="hover:text-blue-600 hover:underline">
            Aviso de privacidad
          </Link>
        </nav>
      </div>
    </footer>
  )
}
