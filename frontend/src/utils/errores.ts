export const MENSAJE_LIMITE_SOLICITUDES =
  'Hiciste demasiados intentos. Espera un minuto antes de volver a intentarlo.'

/** True si el servidor rechazó la solicitud por superar el límite por minuto (429). */
export function esLimiteDeSolicitudes(err: unknown): boolean {
  return (err as { response?: { status?: number } } | null)?.response?.status === 429
}

export const MENSAJE_NO_ES_POLITICA =
  'El texto no parece una política de privacidad: casi no explica qué datos personales se recopilan, ' +
  'para qué se usan ni con quién se comparten, por eso no tiene puntuación. Prueba con la política de ' +
  'privacidad de la app o del sitio.'

export const MENSAJE_ELIMINAR_ANALISIS =
  'Se eliminará de forma definitiva, incluido su reporte. Esta acción no se puede deshacer.'

/** Texto del error que devuelve el servidor, o el mensaje indicado si no hay uno legible. */
export function detalleDeError(err: unknown, porDefecto: string): string {
  if (esLimiteDeSolicitudes(err)) return MENSAJE_LIMITE_SOLICITUDES
  const detalle = (err as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail
  return typeof detalle === 'string' ? detalle : porDefecto
}
