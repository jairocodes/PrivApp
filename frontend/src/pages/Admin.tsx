import Navbar from '@/components/common/Navbar'

export default function Admin() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
        <h1 className="text-xl font-bold text-gray-900 mb-2">Administración</h1>
        <p className="text-sm text-gray-500">
          Desde aquí se accederá a la gestión de usuarios y del corpus normativo.
        </p>
      </main>
    </div>
  )
}
