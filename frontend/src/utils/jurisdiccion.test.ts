import { describe, expect, it } from 'vitest'
import { inferirJurisdiccion } from './jurisdiccion'

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
