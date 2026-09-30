import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 px-4 py-4">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-3 text-xs text-gray-500">
        <span>PrivApp</span>
        <Link to="/aviso-privacidad" className="hover:text-blue-600 hover:underline">
          Aviso de privacidad
        </Link>
      </div>
    </footer>
  )
}
