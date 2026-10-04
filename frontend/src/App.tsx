import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { TemaProvider } from '@/context/TemaContext'
import ProtectedRoute from '@/components/common/ProtectedRoute'
import AdminRoute from '@/components/common/AdminRoute'
import AppLayout from '@/components/layout/AppLayout'
import LayoutPublico from '@/components/layout/LayoutPublico'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Dashboard from '@/pages/Dashboard'
import Ingesta from '@/pages/Ingesta'
import Resultados from '@/pages/Resultados'
import Historial from '@/pages/Historial'
import Admin from '@/pages/Admin'
import AdminUsuarios from '@/pages/AdminUsuarios'
import AdminCorpus from '@/pages/AdminCorpus'
import AvisoPrivacidad from '@/pages/AvisoPrivacidad'
import Glosario from '@/pages/Glosario'
import Perfil from '@/pages/Perfil'

export default function App() {
  return (
    <TemaProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<LayoutPublico />}>
              <Route path="/login" element={<Login />} />
              <Route path="/registro" element={<Register />} />
            </Route>
            <Route element={<AppLayout />}>
              <Route path="/aviso-privacidad" element={<AvisoPrivacidad />} />
              <Route path="/glosario" element={<Glosario />} />
              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/analizar" element={<Ingesta />} />
                <Route path="/resultados/:id" element={<Resultados />} />
                <Route path="/historial" element={<Historial />} />
                <Route path="/perfil" element={<Perfil />} />
              </Route>
              <Route element={<AdminRoute />}>
                <Route path="/admin" element={<Admin />} />
                <Route path="/admin/usuarios" element={<AdminUsuarios />} />
                <Route path="/admin/corpus" element={<AdminCorpus />} />
              </Route>
            </Route>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TemaProvider>
  )
}
