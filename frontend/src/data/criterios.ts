/**
 * Explicación en lenguaje sencillo de cada criterio de la rúbrica con la que el
 * servidor clasifica los hallazgos (backend: analisis_service.CRITERIOS). Se
 * muestra como "Por qué" en cada hallazgo; completa la frase "La política…".
 */
export const POR_QUE_CRITERIO: Record<string, string> = {
  A1: 'recopila datos biométricos, como tu rostro, tus huellas o tu voz',
  A2: 'graba audio o video sin decir para qué, o de forma pasiva',
  A3: 'trata datos de salud u otros datos sensibles sin justificarlo',
  A4: 'comparte tus datos con terceros que no identifica',
  A5: 'envía tus datos a países sin leyes de protección equivalentes',
  A6: 'guarda tus datos sin límite de tiempo',
  A7: 'no ofrece una forma de consultar, corregir o borrar tus datos',
  A8: 'recopila datos de menores sin verificar el permiso de sus padres',
  A9: 'da por hecho que aceptas solo por usar el servicio',
  A10: 'puede cambiar la política sin avisarte',
  M1: 'explica para qué usa tus datos de forma amplia o ambigua',
  M2: 'no deja claro cuánto tiempo guarda tus datos',
  M3: 'complica ejercer tus derechos o no da plazos para responder',
  M4: 'envía datos a otros países con garantías generales, sin decir cuáles',
  M5: 'tiene otra práctica que reduce tu control sobre tus datos',
  B1: 'explica con claridad para qué usa tus datos',
  B2: 'dice cuánto tiempo guarda tus datos',
  B3: 'explica cómo ejercer tus derechos y a quién contactar',
  B4: 'avisa antes de cambiar la política',
}

export function porQueDelCriterio(criterio?: string | null): string | null {
  if (!criterio) return null
  const explicacion = POR_QUE_CRITERIO[criterio]
  return explicacion ? `La política ${explicacion} (criterio ${criterio}).` : null
}
