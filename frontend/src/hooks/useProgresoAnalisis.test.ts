import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { analisisApi } from '@/api/analisis'
import type { AnalisisEstado } from '@/types/analisis'
import { useProgresoAnalisis } from './useProgresoAnalisis'

vi.mock('@/api/analisis', () => ({ analisisApi: { consultarEstado: vi.fn() } }))

const respuesta = (data: AnalisisEstado) =>
  ({ data }) as Awaited<ReturnType<typeof analisisApi.consultarEstado>>

describe('useProgresoAnalisis', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('sondea el estado y se detiene cuando el análisis se completa', async () => {
    vi.mocked(analisisApi.consultarEstado)
      .mockResolvedValueOnce(respuesta({ estado: 'procesando', seccion_actual: 1, secciones_total: 3 }))
      .mockResolvedValueOnce(respuesta({ estado: 'completado', seccion_actual: 3, secciones_total: 3 }))

    const { result } = renderHook(() => useProgresoAnalisis('9'))

    await act(async () => {})
    expect(result.current).toEqual({ estado: 'procesando', seccionActual: 1, seccionesTotal: 3, motivo: null })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500)
    })
    expect(result.current.estado).toBe('completado')
    expect(result.current.seccionActual).toBe(3)

    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000)
    })
    expect(analisisApi.consultarEstado).toHaveBeenCalledTimes(2)
    expect(analisisApi.consultarEstado).toHaveBeenCalledWith('9')
  })

  it('pasa a estado de error si la consulta falla', async () => {
    vi.mocked(analisisApi.consultarEstado).mockRejectedValue(new Error('red'))

    const { result } = renderHook(() => useProgresoAnalisis('9'))

    await act(async () => {})
    expect(result.current.estado).toBe('error')

    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000)
    })
    expect(analisisApi.consultarEstado).toHaveBeenCalledTimes(1)
  })

  it('no consulta nada sin identificador de análisis', () => {
    renderHook(() => useProgresoAnalisis(undefined))
    expect(analisisApi.consultarEstado).not.toHaveBeenCalled()
  })
})
