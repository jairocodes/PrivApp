import { describe, expect, it } from 'vitest'
import type { Hallazgo, SeccionAnalizada } from '@/types/analisis'
import { SIN_FILTRO, contarHallazgos, filtrarSecciones, hallazgoCoincide, hayFiltroActivo } from './filtrosHallazgos'

const cita = (documento: string) => ({ documento, referencia: 'Art. 1', fragmento_relevante: 'texto' })

const hallazgo = (nivel: Hallazgo['nivel'], documentos: string[], descripcion: string = nivel): Hallazgo => ({
  tipo: 'riesgo',
  descripcion,
  nivel,
  fuentes_normativas: documentos.map(cita),
})

const SECCIONES: SeccionAnalizada[] = [
  {
    categoria_opp115: 'First Party',
    titulo: 'Recopilación',
    texto_original: '',
    hallazgos: [hallazgo('alto', ['RGPD.pdf'], 'alto-internacional'), hallazgo('bajo', ['Constitución de Guatemala'], 'bajo-guatemala')],
  },
  {
    categoria_opp115: 'Third Party',
    titulo: 'Terceros',
    texto_original: '',
    hallazgos: [hallazgo('alto', ['Decreto 57-2008.pdf', 'RGPD.pdf'], 'alto-mixto'), hallazgo('medio', [], 'medio-sin-cita')],
  },
  { categoria_opp115: 'Other', titulo: 'Contacto', texto_original: '', hallazgos: [] },
]

const descripciones = (secciones: ReturnType<typeof filtrarSecciones>) =>
  secciones.flatMap(({ seccion }) => seccion.hallazgos.map((h) => h.descripcion))

describe('filtro de hallazgos', () => {
  it('sin filtro devuelve todas las secciones numeradas', () => {
    const resultado = filtrarSecciones(SECCIONES, SIN_FILTRO)
    expect(resultado.map((s) => s.indice)).toEqual([1, 2, 3])
    expect(hayFiltroActivo(SIN_FILTRO)).toBe(false)
  })

  it('por nivel de riesgo', () => {
    const resultado = filtrarSecciones(SECCIONES, { nivel: 'alto', jurisdiccion: '' })
    expect(descripciones(resultado)).toEqual(['alto-internacional', 'alto-mixto'])
  })

  it('por jurisdicción de las citas', () => {
    const resultado = filtrarSecciones(SECCIONES, { nivel: '', jurisdiccion: 'guatemala' })
    expect(descripciones(resultado)).toEqual(['bajo-guatemala', 'alto-mixto'])
  })

  it('combina nivel y jurisdicción', () => {
    const resultado = filtrarSecciones(SECCIONES, { nivel: 'alto', jurisdiccion: 'guatemala' })
    expect(descripciones(resultado)).toEqual(['alto-mixto'])
  })

  it('omite las secciones sin coincidencias y conserva su número original', () => {
    const resultado = filtrarSecciones(SECCIONES, { nivel: 'medio', jurisdiccion: '' })
    expect(resultado).toHaveLength(1)
    expect(resultado[0].indice).toBe(2)
    expect(resultado[0].seccion.titulo).toBe('Terceros')
  })

  it('un hallazgo sin citas no coincide con ninguna jurisdicción', () => {
    expect(hallazgoCoincide(hallazgo('medio', []), { nivel: '', jurisdiccion: 'internacional' })).toBe(false)
  })

  it('usa la jurisdicción guardada con la cita', () => {
    const conJurisdiccion: Hallazgo = {
      ...hallazgo('alto', []),
      fuentes_normativas: [{ ...cita('Documento nuevo'), jurisdiccion: 'guatemala' }],
    }
    expect(hallazgoCoincide(conJurisdiccion, { nivel: '', jurisdiccion: 'guatemala' })).toBe(true)
    expect(hallazgoCoincide(conJurisdiccion, { nivel: '', jurisdiccion: 'internacional' })).toBe(false)
  })

  it('no modifica las secciones originales', () => {
    filtrarSecciones(SECCIONES, { nivel: 'alto', jurisdiccion: '' })
    expect(contarHallazgos(SECCIONES)).toBe(4)
  })
})
