import { render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { analisisApi } from '@/api/analisis'
import { useAnalisis } from '@/hooks/useAnalisis'
import { useProgresoAnalisis } from '@/hooks/useProgresoAnalisis'
import { analisisEjemplo } from '@/test/fixtures'
import Resultados from './Resultados'

vi.mock('@/components/common/Navbar', () => ({ default: () => null }))
vi.mock('@/hooks/useAnalisis', () => ({ useAnalisis: vi.fn() }))
vi.mock('@/hooks/useProgresoAnalisis', () => ({ useProgresoAnalisis: vi.fn() }))
vi.mock('@/api/analisis', () => ({ analisisApi: { descargarPDF: vi.fn(), eliminar: vi.fn() } }))

const obtener = vi.fn()

function renderResultados() {
  render(
    <MemoryRouter initialEntries={['/resultados/7']}>
      <Routes>
        <Route path="/resultados/:id" element={<Resultados />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Resultados', () => {
  beforeEach(() => {
    vi.mocked(useAnalisis).mockReturnValue({ resultado: null, isLoading: false, error: null, obtener })
  })

  it('muestra la vista de progreso mientras el análisis se procesa', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'procesando', seccionActual: 1, seccionesTotal: 3, motivo: null })
    renderResultados()

    expect(screen.getByText('Analizando la política: 1 de 3 secciones listas...')).toBeInTheDocument()
    expect(obtener).not.toHaveBeenCalled()
  })

  it('muestra un mensaje si el análisis terminó con error', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'error', seccionActual: 0, seccionesTotal: null, motivo: null })
    renderResultados()

    expect(screen.getByText('Ocurrió un error durante el análisis. Intenta nuevamente.')).toBeInTheDocument()
  })

  it('explica que el texto no parece una política de privacidad', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({
      estado: 'error', seccionActual: 3, seccionesTotal: 3, motivo: 'no_es_politica',
    })
    renderResultados()

    expect(screen.getByRole('alert')).toHaveTextContent('El texto no parece una política de privacidad')
    expect(screen.queryByText('Ocurrió un error durante el análisis. Intenta nuevamente.')).not.toBeInTheDocument()
  })

  it('pide el resultado al completarse el análisis', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 3, seccionesTotal: 3, motivo: null })
    renderResultados()

    expect(obtener).toHaveBeenCalledWith('7')
  })

  it('presenta el panel con puntuación accesible, secciones y recomendaciones', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 1, seccionesTotal: 1, motivo: null })
    vi.mocked(useAnalisis).mockReturnValue({ resultado: analisisEjemplo, isLoading: false, error: null, obtener })
    renderResultados()

    expect(
      screen.getByRole('img', { name: 'Puntuación de riesgo: 90 de 100, Riesgo Alto' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Esta política presenta 1 hallazgo(s) de riesgo alto.')).toBeInTheDocument()
    expect(screen.getByText('Compartición con terceros')).toBeInTheDocument()
    expect(screen.getByText('Revisa con quién se comparten tus datos.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Descargar PDF/ })).toBeInTheDocument()
  })

  it('explica el límite de descargas del PDF ante un 429', async () => {
    vi.mocked(analisisApi.descargarPDF).mockRejectedValue({ response: { status: 429 } })
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 1, seccionesTotal: 1, motivo: null })
    vi.mocked(useAnalisis).mockReturnValue({ resultado: analisisEjemplo, isLoading: false, error: null, obtener })
    renderResultados()

    await userEvent.click(screen.getByRole('button', { name: /Descargar PDF/ }))

    expect(await screen.findByText('Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo.')).toBeInTheDocument()
  })

  it('ofrece ayuda del glosario para el nivel, la puntuación y las recomendaciones', () => {
    vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 1, seccionesTotal: 1, motivo: null })
    vi.mocked(useAnalisis).mockReturnValue({ resultado: analisisEjemplo, isLoading: false, error: null, obtener })
    renderResultados()

    expect(screen.getByRole('button', { name: 'Qué significa «Nivel de riesgo»' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Qué significa «Puntuación de riesgo»' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Qué significa «Recomendación»' })).toBeInTheDocument()
  })

  describe('eliminación desde el detalle', () => {
    function renderConHistorial() {
      render(
        <MemoryRouter initialEntries={['/resultados/7']}>
          <Routes>
            <Route path="/resultados/:id" element={<Resultados />} />
            <Route path="/historial" element={<p>Pantalla de historial</p>} />
          </Routes>
        </MemoryRouter>,
      )
    }

    beforeEach(() => {
      vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 1, seccionesTotal: 1, motivo: null })
      vi.mocked(useAnalisis).mockReturnValue({ resultado: analisisEjemplo, isLoading: false, error: null, obtener })
    })

    it('elimina tras confirmar y vuelve al historial', async () => {
      vi.mocked(analisisApi.eliminar).mockResolvedValue({} as Awaited<ReturnType<typeof analisisApi.eliminar>>)
      renderConHistorial()

      await userEvent.click(screen.getByRole('button', { name: 'Eliminar análisis' }))
      const dialogo = screen.getByRole('alertdialog', { name: '¿Eliminar este análisis?' })
      expect(dialogo).toHaveTextContent('no se puede deshacer')
      await userEvent.click(within(dialogo).getByRole('button', { name: 'Eliminar' }))

      expect(analisisApi.eliminar).toHaveBeenCalledWith('7')
      expect(await screen.findByText('Pantalla de historial')).toBeInTheDocument()
    })

    it('cancelar no elimina', async () => {
      renderConHistorial()

      await userEvent.click(screen.getByRole('button', { name: 'Eliminar análisis' }))
      await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

      expect(analisisApi.eliminar).not.toHaveBeenCalled()
      expect(screen.getByRole('button', { name: 'Eliminar análisis' })).toBeInTheDocument()
    })

    it('muestra el error si no se puede eliminar', async () => {
      vi.mocked(analisisApi.eliminar).mockRejectedValue({ response: { status: 404, data: { detail: 'Análisis no encontrado.' } } })
      renderConHistorial()

      await userEvent.click(screen.getByRole('button', { name: 'Eliminar análisis' }))
      await userEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Eliminar' }))

      expect(await screen.findByText('Análisis no encontrado.')).toBeInTheDocument()
    })
  })

  describe('filtro de hallazgos', () => {
    const analisisConVarios = {
      ...analisisEjemplo,
      secciones_analizadas: [
        analisisEjemplo.secciones_analizadas[0],
        {
          categoria_opp115: 'Data Retention',
          titulo: 'Conservación',
          texto_original: '',
          hallazgos: [{
            tipo: 'riesgo' as const,
            descripcion: 'Conserva los datos sin plazo.',
            nivel: 'medio' as const,
            fuentes_normativas: [{ documento: 'Decreto 57-2008.pdf', referencia: 'Art. 9', fragmento_relevante: 'x' }],
          }],
        },
      ],
    }

    beforeEach(() => {
      vi.mocked(useProgresoAnalisis).mockReturnValue({ estado: 'completado', seccionActual: 2, seccionesTotal: 2, motivo: null })
      vi.mocked(useAnalisis).mockReturnValue({ resultado: analisisConVarios, isLoading: false, error: null, obtener })
    })

    it('por nivel reduce la lista de hallazgos', async () => {
      renderResultados()
      expect(screen.getByText('Mostrando 3 de 3 hallazgos')).toBeInTheDocument()

      await userEvent.selectOptions(screen.getByLabelText('Nivel de riesgo'), 'medio')

      expect(screen.getByText('Mostrando 1 de 3 hallazgos')).toBeInTheDocument()
      expect(screen.getByText('Conserva los datos sin plazo.')).toBeInTheDocument()
      expect(screen.queryByText('Compartición con terceros')).not.toBeInTheDocument()
    })

    it('por jurisdicción reduce la lista de hallazgos', async () => {
      renderResultados()

      await userEvent.selectOptions(screen.getByLabelText('Jurisdicción de la cita'), 'internacional')

      expect(screen.getByText('Mostrando 1 de 3 hallazgos')).toBeInTheDocument()
      expect(screen.getByText('Tus datos pueden llegar a empresas que no conoces.')).toBeInTheDocument()
      expect(screen.queryByText('Conservación')).not.toBeInTheDocument()
    })

    it('limpiar muestra todos los hallazgos de nuevo', async () => {
      renderResultados()
      await userEvent.selectOptions(screen.getByLabelText('Nivel de riesgo'), 'medio')

      await userEvent.click(screen.getByRole('button', { name: 'Limpiar filtros' }))

      expect(screen.getByText('Mostrando 3 de 3 hallazgos')).toBeInTheDocument()
      expect(screen.getByLabelText('Nivel de riesgo')).toHaveValue('')
      expect(screen.getByText('Compartición con terceros')).toBeInTheDocument()
    })

    it('avisa cuando ningún hallazgo coincide', async () => {
      renderResultados()
      await userEvent.selectOptions(screen.getByLabelText('Nivel de riesgo'), 'bajo')
      await userEvent.selectOptions(screen.getByLabelText('Jurisdicción de la cita'), 'guatemala')

      expect(screen.getByText('Ningún hallazgo coincide con los filtros.')).toBeInTheDocument()
      await userEvent.click(screen.getByRole('button', { name: 'Mostrar todos los hallazgos' }))
      expect(screen.getByText('Mostrando 3 de 3 hallazgos')).toBeInTheDocument()
    })

    it('el resumen general no cambia al filtrar', async () => {
      renderResultados()
      await userEvent.selectOptions(screen.getByLabelText('Nivel de riesgo'), 'medio')

      expect(screen.getByRole('img', { name: 'Puntuación de riesgo: 90 de 100, Riesgo Alto' })).toBeInTheDocument()
    })
  })
})
