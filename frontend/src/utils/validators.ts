export const MIN_TEXTO = 200
export const MAX_TEXTO = 50000

export function validarTextoPolítica(texto: string): string | null {
  if (texto.trim().length < MIN_TEXTO)
    return `El texto debe tener al menos ${MIN_TEXTO} caracteres.`
  if (texto.length > MAX_TEXTO)
    return `El texto no puede superar los ${MAX_TEXTO.toLocaleString()} caracteres.`
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
