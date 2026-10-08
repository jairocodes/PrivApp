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

  it('tiene las 22 entradas aprobadas, todas con definición en texto plano', () => {
    expect(GLOSARIO).toHaveLength(22)
    for (const entrada of GLOSARIO) {
      expect(entrada.definicion.length).toBeGreaterThan(40)
      expect(entrada.definicion).not.toContain('PENDIENTE_CONTENIDO')
      expect(entrada.definicion).not.toMatch(/[<>*_#]|https?:/)
    }
  })

  it('usa «Puntuación de riesgo» e incluye «Cláusula» y «Recomendación»', () => {
    const terminos = GLOSARIO.map((e) => e.termino)
    expect(terminos).toEqual(expect.arrayContaining(['Puntuación de riesgo', 'Cláusula', 'Recomendación']))
    expect(terminos).not.toContain('Puntaje de riesgo')
  })

  it('los términos con ayuda contextual en los resultados tienen su entrada', () => {
    for (const termino of [
      'Nivel de riesgo',
      'Puntuación de riesgo',
      'Referencia internacional',
      'Sin respaldo en el corpus normativo',
      'Recomendación',
      ...TIPOS_TRATAMIENTO,
    ]) {
      expect(entradaPorTermino(termino), termino).toBeDefined()
    }
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
