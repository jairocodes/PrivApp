import { describe, expect, it } from 'vitest'
import { GLOSARIO, buscarEnGlosario, entradaPorTermino, normalizar } from './glosario'

const TIPOS_TRATAMIENTO = [
  'Recopilación de datos personales',
  'Uso y finalidad de los datos',
  'Transferencia de datos a terceros',
  'Tiempo de conservación de los datos',
  'Seguridad de los datos',
  'Derechos del usuario sobre sus datos',
  'Cambios en la política',
  'Otro',
]

describe('glosario', () => {
  it('incluye los ocho tipos de tratamiento con sus textos exactos', () => {
    const terminos = GLOSARIO.map((e) => e.termino)
    for (const tipo of TIPOS_TRATAMIENTO) expect(terminos).toContain(tipo)
  })

  it('los identificadores son únicos', () => {
    const ids = GLOSARIO.map((e) => e.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('normaliza mayúsculas y acentos', () => {
    expect(normalizar('  Política de Conservación ')).toBe('politica de conservacion')
  })

  it('busca sin distinguir mayúsculas ni acentos', () => {
    expect(buscarEnGlosario('JURISDICCION').map((e) => e.termino)).toEqual(['Jurisdicción'])
    expect(buscarEnGlosario('conservacion').map((e) => e.termino)).toEqual([
      'Tiempo de conservación de los datos',
    ])
  })

  it('una búsqueda vacía devuelve todo el glosario', () => {
    expect(buscarEnGlosario('   ')).toHaveLength(GLOSARIO.length)
  })

  it('busca también en las definiciones', () => {
    const entradas = [{ id: 'x', termino: 'Cookie', definicion: 'Archivo pequeño que guarda el navegador.' }]
    expect(buscarEnGlosario('navegador', entradas)).toEqual(entradas)
  })

  it('encuentra una entrada por su término', () => {
    expect(entradaPorTermino('transferencia de datos a terceros')?.id).toBe('transferencia-de-datos-a-terceros')
    expect(entradaPorTermino('inexistente')).toBeUndefined()
  })
})
