// Glosario de términos en lenguaje sencillo (HU-24). Contenido estático: no usa el
// modelo de lenguaje. Las definiciones son el contenido aprobado por el responsable
// del proyecto: no modificarlas sin su aprobación. La ayuda contextual busca cada
// entrada por su término exacto (ver AyudaGlosario).

export interface EntradaGlosario {
  id: string
  termino: string
  definicion: string
}

export const GLOSARIO: EntradaGlosario[] = [
  {
    id: 'politica-de-privacidad',
    termino: 'Política de privacidad',
    definicion:
      'Documento en el que una aplicación o sitio web explica qué datos personales recopila, cómo los usa, con quién los comparte, cuánto tiempo los guarda y qué control tiene usted sobre ellos. Aceptarla sin leerla significa aceptar condiciones que quizá no conoce.',
  },
  {
    id: 'datos-personales',
    termino: 'Datos personales',
    definicion:
      'Toda información que permite identificarle a usted, directa o indirectamente, como su nombre, correo electrónico, dirección, número de teléfono o ubicación.',
  },
  {
    id: 'tratamiento-de-datos',
    termino: 'Tratamiento de datos',
    definicion:
      'Todo lo que una plataforma hace con sus datos personales: recopilarlos, usarlos, almacenarlos, compartirlos o eliminarlos.',
  },
  {
    id: 'clausula',
    termino: 'Cláusula',
    definicion:
      'Cada parte de una política de privacidad que establece una condición específica, por ejemplo qué datos se recopilan o con quién se comparten.',
  },
  {
    id: 'hallazgo',
    termino: 'Hallazgo',
    definicion:
      'Cada punto relevante que PrivApp encuentra al analizar una sección de la política. Puede señalar un riesgo, una práctica de transparencia o información neutral, y tiene un nivel (bajo, medio o alto) y un tipo de tratamiento de datos.',
  },
  {
    id: 'nivel-de-riesgo',
    termino: 'Nivel de riesgo',
    definicion:
      'Calificación general de la política: bajo, medio o alto. Es alto cuando hay dos o más hallazgos de nivel alto o la puntuación es de 75 o más, y medio cuando hay dos o más hallazgos de nivel medio o la puntuación es de 25 o más. Por eso, una política puede tener nivel alto aunque su puntuación sea baja.',
  },
  {
    id: 'puntuacion-de-riesgo',
    termino: 'Puntuación de riesgo',
    definicion:
      'Número de 0 a 100 que resume qué tan riesgosa es la política para su privacidad: mientras mayor sea, mayor es el riesgo. Se calcula a partir del nivel de los hallazgos respaldados por el corpus normativo.',
  },
  {
    id: 'cita-normativa',
    termino: 'Cita normativa',
    definicion:
      'Fragmento real de una ley, norma o estándar que respalda un hallazgo, con el nombre del documento del que proviene. PrivApp no redacta estas citas: las toma de su corpus normativo, que es el conjunto de leyes y normas que utiliza como referencia.',
  },
  {
    id: 'jurisdiccion',
    termino: 'Jurisdicción',
    definicion:
      'Ámbito al que pertenece una norma citada: Guatemala, internacional o estándar técnico. Le indica si la norma es ley en Guatemala o una referencia de otro país u organismo.',
  },
  {
    id: 'referencia-internacional',
    termino: 'Referencia internacional',
    definicion:
      'Norma de otro país u organismo internacional que PrivApp muestra como buena práctica. No es ley vigente en Guatemala, pero ayuda a entender cómo se protege la privacidad en otros lugares.',
  },
  {
    id: 'sin-respaldo-en-el-corpus-normativo',
    termino: 'Sin respaldo en el corpus normativo',
    definicion:
      'Indica que PrivApp detectó un posible riesgo, pero ninguna norma de su corpus lo respalda. El hallazgo se muestra para su información, pero no se toma en cuenta en la puntuación ni en el nivel de riesgo.',
  },
  {
    id: 'recomendacion',
    termino: 'Recomendación',
    definicion:
      'Sugerencia práctica que PrivApp le ofrece para proteger su privacidad frente a los riesgos encontrados en la política analizada.',
  },
  {
    id: 'consentimiento',
    termino: 'Consentimiento',
    definicion:
      'Su autorización para que una plataforma trate sus datos personales. Para ser válido debe darse de forma libre, clara e informada, es decir, sabiendo realmente qué está aceptando.',
  },
  {
    id: 'terceros',
    termino: 'Terceros',
    definicion:
      'Personas, empresas u organizaciones distintas de usted y de la plataforma que utiliza, con las que esta puede compartir sus datos, como socios comerciales o anunciantes.',
  },
  // Los ocho tipos de tratamiento de datos (RN-08), con los textos exactos de la lista cerrada.
  {
    id: 'recopilacion-de-datos-personales',
    termino: 'Recopilación de datos personales',
    definicion:
      'Cláusula que indica qué datos obtiene la plataforma sobre usted, por ejemplo su nombre, sus contactos o su ubicación, y de qué forma los obtiene.',
  },
  {
    id: 'uso-y-finalidad-de-los-datos',
    termino: 'Uso y finalidad de los datos',
    definicion:
      'Cláusula que explica para qué utilizará la plataforma sus datos, por ejemplo para ofrecerle el servicio, enviarle publicidad o mejorar sus productos.',
  },
  {
    id: 'transferencia-de-datos-a-terceros',
    termino: 'Transferencia de datos a terceros',
    definicion:
      'Cláusula que indica si la plataforma comparte o entrega sus datos a otras empresas u organizaciones, y con qué fines. Es uno de los puntos en los que usted pierde más control sobre su información.',
  },
  {
    id: 'tiempo-de-conservacion-de-los-datos',
    termino: 'Tiempo de conservación de los datos',
    definicion:
      'Cláusula que indica durante cuánto tiempo la plataforma guardará sus datos antes de eliminarlos.',
  },
  {
    id: 'seguridad-de-los-datos',
    termino: 'Seguridad de los datos',
    definicion:
      'Cláusula que describe las medidas que la plataforma dice aplicar para proteger sus datos contra accesos no autorizados, pérdidas o filtraciones.',
  },
  {
    id: 'derechos-del-usuario-sobre-sus-datos',
    termino: 'Derechos del usuario sobre sus datos',
    definicion:
      'Cláusula que le informa lo que usted puede hacer con sus datos, como conocerlos, corregirlos, solicitar su eliminación u oponerse a su uso, y cómo solicitarlo.',
  },
  {
    id: 'cambios-en-la-politica',
    termino: 'Cambios en la política',
    definicion:
      'Cláusula que indica cómo y cuándo la plataforma puede modificar su política de privacidad, y si le avisará cuando lo haga.',
  },
  {
    id: 'otro',
    termino: 'Otro',
    definicion:
      'Categoría para los hallazgos que no corresponden a ninguno de los demás tipos de tratamiento de datos.',
  },
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
