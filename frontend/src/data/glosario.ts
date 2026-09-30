// Glosario de términos en lenguaje sencillo (HU-24). Contenido estático: no usa el
// modelo de lenguaje. Las definiciones las redacta el responsable del proyecto; la
// lista de términos es una propuesta basada en los que aparecen en los resultados.

export const DEFINICION_PENDIENTE = 'PENDIENTE_CONTENIDO'

export interface EntradaGlosario {
  id: string
  termino: string
  definicion: string
}

export const GLOSARIO: EntradaGlosario[] = [
  { id: 'politica-de-privacidad', termino: 'Política de privacidad', definicion: DEFINICION_PENDIENTE },
  { id: 'datos-personales', termino: 'Datos personales', definicion: DEFINICION_PENDIENTE },
  { id: 'tratamiento-de-datos', termino: 'Tratamiento de datos', definicion: DEFINICION_PENDIENTE },
  { id: 'hallazgo', termino: 'Hallazgo', definicion: DEFINICION_PENDIENTE },
  { id: 'nivel-de-riesgo', termino: 'Nivel de riesgo', definicion: DEFINICION_PENDIENTE },
  { id: 'puntaje-de-riesgo', termino: 'Puntaje de riesgo', definicion: DEFINICION_PENDIENTE },
  { id: 'cita-normativa', termino: 'Cita normativa', definicion: DEFINICION_PENDIENTE },
  { id: 'jurisdiccion', termino: 'Jurisdicción', definicion: DEFINICION_PENDIENTE },
  { id: 'referencia-internacional', termino: 'Referencia internacional', definicion: DEFINICION_PENDIENTE },
  { id: 'consentimiento', termino: 'Consentimiento', definicion: DEFINICION_PENDIENTE },
  { id: 'terceros', termino: 'Terceros', definicion: DEFINICION_PENDIENTE },
  // Los ocho tipos de tratamiento de datos (RN-08), con los textos exactos de la lista cerrada.
  { id: 'recopilacion-de-datos-personales', termino: 'Recopilación de datos personales', definicion: DEFINICION_PENDIENTE },
  { id: 'uso-y-finalidad-de-los-datos', termino: 'Uso y finalidad de los datos', definicion: DEFINICION_PENDIENTE },
  { id: 'transferencia-de-datos-a-terceros', termino: 'Transferencia de datos a terceros', definicion: DEFINICION_PENDIENTE },
  { id: 'tiempo-de-conservacion-de-los-datos', termino: 'Tiempo de conservación de los datos', definicion: DEFINICION_PENDIENTE },
  { id: 'seguridad-de-los-datos', termino: 'Seguridad de los datos', definicion: DEFINICION_PENDIENTE },
  { id: 'derechos-del-usuario-sobre-sus-datos', termino: 'Derechos del usuario sobre sus datos', definicion: DEFINICION_PENDIENTE },
  { id: 'cambios-en-la-politica', termino: 'Cambios en la política', definicion: DEFINICION_PENDIENTE },
  { id: 'otro', termino: 'Otro', definicion: DEFINICION_PENDIENTE },
]

/** Minúsculas y sin acentos, para buscar "politica" y encontrar "Política". */
export function normalizar(texto: string): string {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()
}

export function buscarEnGlosario(consulta: string, entradas: EntradaGlosario[] = GLOSARIO): EntradaGlosario[] {
  const buscado = normalizar(consulta)
  if (!buscado) return entradas
  return entradas.filter(
    (e) => normalizar(e.termino).includes(buscado) || normalizar(e.definicion).includes(buscado),
  )
}

export function entradaPorTermino(termino: string): EntradaGlosario | undefined {
  const buscado = normalizar(termino)
  return GLOSARIO.find((e) => normalizar(e.termino) === buscado)
}
