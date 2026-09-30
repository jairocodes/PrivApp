// Misma regla que el servidor (RN-01); el servidor la aplica sobre el texto limpio.
export const MIN_TEXTO = 200
export const MIN_PALABRAS = 40
export const MAX_TEXTO = 200000

export function contarPalabras(texto: string): number {
  const limpio = texto.trim()
  return limpio ? limpio.split(/\s+/).length : 0
}

export function validarTextoPolítica(texto: string): string | null {
  const limpio = texto.trim()
  if (limpio.length > MAX_TEXTO)
    return `El texto no puede superar los ${MAX_TEXTO.toLocaleString()} caracteres.`
  if (limpio.length < MIN_TEXTO || contarPalabras(limpio) < MIN_PALABRAS)
    return `El texto debe tener al menos ${MIN_TEXTO} caracteres y ${MIN_PALABRAS} palabras.`
  return null
}

export const TAMANO_MAXIMO_ARCHIVO = 5 * 1024 * 1024
const EXTENSIONES_ARCHIVO = ['.pdf', '.txt']

export function validarArchivo(archivo: File): string | null {
  const nombre = archivo.name.toLowerCase()
  if (!EXTENSIONES_ARCHIVO.some((ext) => nombre.endsWith(ext)))
    return 'Solo se aceptan archivos PDF (.pdf) o de texto plano (.txt).'
  if (archivo.size > TAMANO_MAXIMO_ARCHIVO) return 'El archivo supera el tamaño máximo de 5 MB.'
  if (archivo.size === 0) return 'El archivo está vacío.'
  return null
}

export function validarURL(url: string): string | null {
  try {
    const parsed = new URL(url)
    if (!['http:', 'https:'].includes(parsed.protocol))
      return 'La URL debe comenzar con http:// o https://'
    return null
  } catch {
    return 'Ingresa una URL válida (ej: https://ejemplo.com/privacidad).'
  }
}

export function validarPassword(password: string): string | null {
  if (password.length < 8) return 'La contraseña debe tener al menos 8 caracteres.'
  if (!/[A-Z]/.test(password)) return 'Debe contener al menos una letra mayúscula.'
  if (!/[0-9]/.test(password)) return 'Debe contener al menos un número.'
  return null
}
