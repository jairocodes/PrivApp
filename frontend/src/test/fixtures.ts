import type { AnalisisResult, SeccionAnalizada } from '@/types/analisis'
import type { AuthContextValue, User } from '@/types/auth'
import { vi } from 'vitest'

export const seccionEjemplo: SeccionAnalizada = {
  categoria_opp115: 'Third Party Sharing/Collection',
  titulo: 'Compartición con terceros',
  texto_original: 'Podemos compartir tus datos con socios comerciales.',
  hallazgos: [
    {
      tipo: 'riesgo',
      descripcion: 'Tus datos pueden llegar a empresas que no conoces.',
      nivel: 'alto',
      tipo_tratamiento: 'Transferencia de datos a terceros',
      fuentes_normativas: [
        {
          documento: 'RGPD',
          referencia: 'Art. 44',
          fragmento_relevante: 'Transferencias de datos personales a terceros países.',
        },
      ],
    },
    {
      tipo: 'transparencia',
      descripcion: 'Se identifica al responsable del tratamiento.',
      nivel: 'bajo',
      fuentes_normativas: [],
    },
  ],
}

export const analisisEjemplo: AnalisisResult = {
  id_analisis: '7',
  fecha: '2026-09-01T15:30:00Z',
  resumen_general: {
    nivel_riesgo_global: 'alto',
    puntaje: 90,
    comentario_breve: 'Esta política presenta 1 hallazgo(s) de riesgo alto.',
  },
  secciones_analizadas: [seccionEjemplo],
  recomendaciones: ['Revisa con quién se comparten tus datos.'],
}

export function crearAuthValue(parcial: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    user: null,
    token: null,
    isLoading: false,
    login: vi.fn().mockResolvedValue(undefined),
    register: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn(),
    actualizarPerfil: vi.fn().mockResolvedValue(undefined),
    cambiarPassword: vi.fn().mockResolvedValue(undefined),
    eliminarCuenta: vi.fn().mockResolvedValue(undefined),
    ...parcial,
  }
}

export const usuarioComun: User = { id: 1, nombre: 'Ana', email: 'ana@privapp.test', role: 'usuario' }

export const administrador: User = {
  id: 2,
  nombre: 'Admin',
  email: 'admin@privapp.test',
  role: 'administrador',
}
