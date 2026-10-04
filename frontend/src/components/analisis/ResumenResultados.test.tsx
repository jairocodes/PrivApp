import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Hallazgo, ResumenGeneral, SeccionAnalizada } from '@/types/analisis'
import { describirConteo, explicarNivel, riesgosPorTratamiento } from '@/utils/resumenResultados'
import MedidorRiesgo from './MedidorRiesgo'
import PorQueResultado from './PorQueResultado'
import ResumenTratamiento from './ResumenTratamiento'

function hallazgo(nivel: Hallazgo['nivel'], extra: Partial<Hallazgo> = {}): Hallazgo {
  return {
    tipo: nivel === 'bajo' ? 'transparencia' : 'riesgo',
    descripcion: `Hallazgo ${nivel}`,
    nivel,
    fuentes_normativas: [],
    tipo_tratamiento: 'Transferencia de datos a terceros',
    ...extra,
  }
}

function seccion(hallazgos: Hallazgo[], extra: Partial<SeccionAnalizada> = {}): SeccionAnalizada {
  return { categoria_opp115: 'Other', titulo: 'Sección', texto_original: '', hallazgos, ...extra }
}

const resumen = (nivel: ResumenGeneral['nivel_riesgo_global'], puntaje: number): ResumenGeneral => ({
  nivel_riesgo_global: nivel, puntaje, comentario_breve: 'c',
})

describe('MedidorRiesgo', () => {
  it('dice la puntuación y el nivel en su nombre accesible', () => {
    render(<MedidorRiesgo puntaje={62} nivel="alto" />)
    expect(screen.getByRole('img', { name: 'Puntuación de riesgo: 62 de 100, Riesgo Alto' })).toBeInTheDocument()
  })

  it('no se sale de la escala con valores fuera de rango', () => {
    const { container } = render(<MedidorRiesgo puntaje={140} nivel="alto" />)
    const aguja = container.querySelector('line')!
    expect(Number(aguja.getAttribute('x2'))).toBeGreaterThan(130)
    expect(Number(aguja.getAttribute('y2'))).toBeCloseTo(130, 0)
  })
})

describe('PorQueResultado', () => {
  it('cuenta solo los hallazgos con respaldo de secciones analizadas', () => {
    const secciones = [
      seccion([hallazgo('alto'), hallazgo('alto'), hallazgo('medio', { sin_respaldo: true })]),
      seccion([hallazgo('bajo')]),
      seccion([hallazgo('alto')], { analizada: false }),
    ]
    render(<PorQueResultado resumen={resumen('alto', 70)} secciones={secciones} />)

    expect(screen.getByText('Revisamos 3 secciones y encontramos 3 cláusulas que cuentan para el resultado.')).toBeInTheDocument()
    const filas = screen.getAllByRole('listitem')
    expect(within(filas[0]).getByText('2')).toBeInTheDocument()
    expect(within(filas[1]).getByText('0')).toBeInTheDocument()
    expect(within(filas[2]).getByText('1')).toBeInTheDocument()
    expect(screen.getByText(/hay 2 cláusulas de riesgo alto: con 2 o más/)).toBeInTheDocument()
    expect(screen.getByText(/1 hallazgo sin respaldo en el corpus normativo se muestra, pero no cuenta/)).toBeInTheDocument()
  })

  it.each([
    [resumen('alto', 80), { alto: 1, medio: 0, bajo: 0 }, 'la puntuación (80) es de 75 o más'],
    [resumen('medio', 40), { alto: 0, medio: 3, bajo: 1 }, 'hay 3 cláusulas de riesgo medio'],
    [resumen('medio', 30), { alto: 1, medio: 1, bajo: 0 }, 'la puntuación (30) es de 25 o más'],
    [resumen('bajo', 0), { alto: 0, medio: 0, bajo: 2 }, 'no tiene suficientes cláusulas'],
  ])('explica el nivel con la regla del servidor (%#)', (res, conteo, esperado) => {
    expect(explicarNivel(res, conteo)).toContain(esperado)
  })
})

describe('ResumenTratamiento', () => {
  const hallazgos = [
    hallazgo('medio', { tipo_tratamiento: 'Uso y finalidad de los datos' }),
    hallazgo('medio', { tipo_tratamiento: 'Uso y finalidad de los datos' }),
    hallazgo('alto'),
    hallazgo('medio'),
    hallazgo('bajo', { tipo_tratamiento: 'Derechos del usuario sobre sus datos' }),
  ]

  it('agrupa los riesgos por tipo de tratamiento, primero los de más riesgos altos', () => {
    expect(riesgosPorTratamiento(hallazgos).map((g) => g.tratamiento)).toEqual([
      'Transferencia de datos a terceros',
      'Uso y finalidad de los datos',
    ])
    expect(describirConteo({ alto: 1, medio: 2, bajo: 0 })).toBe('1 alto · 2 medios')
  })

  it('cada ficha lleva a los hallazgos de su tipo', async () => {
    const onVerTratamiento = vi.fn()
    const onVerTodos = vi.fn()
    render(<ResumenTratamiento hallazgos={hallazgos} onVerTratamiento={onVerTratamiento} onVerTodos={onVerTodos} />)

    await userEvent.click(screen.getByRole('button', { name: /Transferencia de datos a terceros\s*1 alto · 1 medio/ }))
    expect(onVerTratamiento).toHaveBeenCalledWith('Transferencia de datos a terceros')

    await userEvent.click(screen.getByRole('button', { name: /Ver todos los hallazgos/ }))
    expect(onVerTodos).toHaveBeenCalled()
  })

  it('sin riesgos no se muestra', () => {
    const { container } = render(
      <ResumenTratamiento hallazgos={[hallazgo('bajo')]} onVerTratamiento={vi.fn()} onVerTodos={vi.fn()} />,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
