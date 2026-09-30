import { describe, expect, it } from 'vitest'
import { MAX_TEXTO, MIN_TEXTO, validarPassword, validarTextoPolítica, validarURL } from './validators'

describe('validarTextoPolítica', () => {
  it('rechaza textos con menos del mínimo de caracteres', () => {
    expect(validarTextoPolítica('a'.repeat(MIN_TEXTO - 1))).toMatch(/al menos 200/)
  })

  it('ignora los espacios de los extremos al medir el mínimo', () => {
    expect(validarTextoPolítica(`   ${'a'.repeat(MIN_TEXTO - 1)}   `)).not.toBeNull()
  })

  it('rechaza textos por encima del máximo', () => {
    expect(validarTextoPolítica('a'.repeat(MAX_TEXTO + 1))).toMatch(/no puede superar/)
  })

  it('acepta textos dentro del rango', () => {
    expect(validarTextoPolítica('a'.repeat(MIN_TEXTO))).toBeNull()
    expect(validarTextoPolítica('a'.repeat(MAX_TEXTO))).toBeNull()
  })
})

describe('validarURL', () => {
  it('acepta direcciones http y https', () => {
    expect(validarURL('https://ejemplo.com/privacidad')).toBeNull()
    expect(validarURL('http://ejemplo.com')).toBeNull()
  })

  it('rechaza otros protocolos', () => {
    expect(validarURL('ftp://ejemplo.com')).toMatch(/http:\/\/ o https:\/\//)
  })

  it('rechaza textos que no son una dirección', () => {
    expect(validarURL('no es una url')).toMatch(/URL válida/)
  })
})

describe('validarPassword', () => {
  it('exige al menos 8 caracteres', () => {
    expect(validarPassword('Abc123')).toMatch(/8 caracteres/)
  })

  it('exige una letra mayúscula', () => {
    expect(validarPassword('abcdefg1')).toMatch(/mayúscula/)
  })

  it('exige un número', () => {
    expect(validarPassword('Abcdefgh')).toMatch(/número/)
  })

  it('acepta una contraseña que cumple las reglas', () => {
    expect(validarPassword('Segura123')).toBeNull()
  })
})
