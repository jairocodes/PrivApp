import { describe, expect, it } from 'vitest'
import {
  MAX_TEXTO,
  MIN_TEXTO,
  contarPalabras,
  validarArchivo,
  validarPassword,
  validarTextoPolítica,
  validarURL,
} from './validators'

/** Texto de `palabras` palabras de 4 letras más `extra` letras en la última. */
const texto = (palabras: number, extra = 0) =>
  Array.from({ length: palabras }, (_, i) => (i === palabras - 1 ? 'aaaa' + 'b'.repeat(extra) : 'aaaa')).join(' ')

describe('validarTextoPolítica', () => {
  it('rechaza textos con menos del mínimo de caracteres', () => {
    // 40 palabras de 4 letras = 199 caracteres
    expect(validarTextoPolítica(texto(40))).toMatch(/al menos 200 caracteres y 40 palabras/)
  })

  it('rechaza textos con menos de 40 palabras aunque superen 200 caracteres', () => {
    expect(validarTextoPolítica('a'.repeat(MIN_TEXTO))).toMatch(/40 palabras/)
    expect(validarTextoPolítica(texto(39, 50))).not.toBeNull()
  })

  it('ignora los espacios de los extremos al medir el mínimo', () => {
    expect(validarTextoPolítica(`   ${texto(40)}   `)).not.toBeNull()
  })

  it('rechaza textos por encima del máximo', () => {
    expect(validarTextoPolítica('a '.repeat(MAX_TEXTO / 2 + 1))).toMatch(/no puede superar/)
  })

  it('acepta textos dentro del rango', () => {
    expect(validarTextoPolítica(texto(40, 1))).toBeNull()
    expect(validarTextoPolítica('a '.repeat(MAX_TEXTO / 2))).toBeNull()
  })

  it('cuenta palabras separadas por cualquier espacio', () => {
    expect(contarPalabras('  uno\ndos\t tres  ')).toBe(3)
    expect(contarPalabras('   ')).toBe(0)
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

describe('validarArchivo', () => {
  const archivo = (nombre: string, bytes: number) => new File([new Uint8Array(bytes)], nombre)

  it('acepta PDF y TXT sin importar mayúsculas', () => {
    expect(validarArchivo(archivo('politica.pdf', 10))).toBeNull()
    expect(validarArchivo(archivo('POLITICA.TXT', 10))).toBeNull()
  })

  it('rechaza otras extensiones', () => {
    expect(validarArchivo(archivo('politica.docx', 10))).toMatch(/Solo se aceptan/)
  })

  it('rechaza archivos vacíos o de más de 5 MB', () => {
    expect(validarArchivo(archivo('politica.pdf', 0))).toBe('El archivo está vacío.')
    expect(validarArchivo(archivo('politica.pdf', 5 * 1024 * 1024))).toBeNull()
    expect(validarArchivo(archivo('politica.pdf', 5 * 1024 * 1024 + 1))).toMatch(/5 MB/)
  })
})
