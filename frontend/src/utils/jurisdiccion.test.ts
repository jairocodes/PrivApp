import { describe, expect, it } from 'vitest'
import { inferirJurisdiccion } from './jurisdiccion'

describe('inferirJurisdiccion', () => {
  it.each([
    ['Constitución Política de la República de Guatemala.pdf', 'guatemala'],
    ['LAIP', 'guatemala'],
    ['El Corpus OPP-115 y su Ontología Estructural.pdf', 'estandar_tecnico'],
    ['tosdr_metodologia.md', 'estandar_tecnico'],
    ['RGPD.pdf', 'internacional'],
    ['Principios generales de protección de datos', 'internacional'],
  ])('%s → %s', (documento, esperada) => {
    expect(inferirJurisdiccion(documento)).toBe(esperada)
  })
})
