import { describe, expect, it } from 'vitest'
import { inferirJurisdiccion, jurisdiccionDeFuente } from './jurisdiccion'

describe('inferirJurisdiccion', () => {
  it.each([
    ['Constitución Política de la República de Guatemala.pdf', 'guatemala'],
    ['LAIP', 'guatemala'],
    ['El Corpus OPP-115 y su Ontología Estructural.pdf', 'estandar_tecnico'],
    ['tosdr_metodologia.md', 'estandar_tecnico'],
    ['Decreto 57-2008 (Ley de Acceso a la Información Pública).pdf', 'guatemala'],
    ['Ley de Acceso a la Información Pública', 'guatemala'],
    ['Metodología, Casuística y Algoritmos del Proyecto ToS;DR.pdf', 'estandar_tecnico'],
    ['RGPD.pdf', 'internacional'],
    ['LOPDP España.pdf', 'internacional'],
    ['Principios generales de protección de datos', 'internacional'],
  ])('%s → %s', (documento, esperada) => {
    expect(inferirJurisdiccion(documento)).toBe(esperada)
  })
})

describe('jurisdiccionDeFuente', () => {
  const fuente = { documento: 'RGPD', referencia: '', fragmento_relevante: '' }

  it('prefiere la jurisdicción guardada con la cita', () => {
    expect(jurisdiccionDeFuente({ ...fuente, jurisdiccion: 'guatemala' })).toBe('guatemala')
  })

  it('en los análisis antiguos la deduce del documento', () => {
    expect(jurisdiccionDeFuente(fuente)).toBe('internacional')
    expect(jurisdiccionDeFuente({ ...fuente, jurisdiccion: null })).toBe('internacional')
  })
})
