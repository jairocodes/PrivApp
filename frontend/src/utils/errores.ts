export const MENSAJE_LIMITE_SOLICITUDES =
  'Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo.'

/** True si el servidor rechazó la solicitud por superar el límite por minuto (429). */
export function esLimiteDeSolicitudes(err: unknown): boolean {
  return (err as { response?: { status?: number } } | null)?.response?.status === 429
}
