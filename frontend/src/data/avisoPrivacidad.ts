// Aviso de privacidad de PrivApp. Texto redactado por el responsable del
// proyecto; los datos entre corchetes (por ejemplo [correo de contacto]) están
// pendientes de completar. Cada afirmación describe lo que hace el sistema: si
// cambia el sistema, hay que revisar este texto.

export interface Enlace {
  texto: string
  url: string
}

export interface Parrafo {
  tipo: 'parrafo'
  /** Inicio en negrita, por ejemplo "Datos de su cuenta." */
  etiqueta?: string
  texto: string
  enlace?: Enlace
}

export interface ElementoLista {
  etiqueta?: string
  texto: string
  enlace?: Enlace
}

export interface Lista {
  tipo: 'lista'
  elementos: ElementoLista[]
}

export interface Tabla {
  tipo: 'tabla'
  encabezados: [string, string]
  filas: [string, string][]
}

export type Bloque = Parrafo | Lista | Tabla

export interface SeccionAviso {
  id: string
  titulo: string
  bloques: Bloque[]
}

export const TITULO_AVISO = 'Aviso de privacidad de PrivApp'
export const ULTIMA_ACTUALIZACION = '[fecha]'
export const CORREO_CONTACTO = 'jairocastillo.code@gmail.com'

export const INTRODUCCION =
  'PrivApp es un sistema web que analiza políticas de privacidad para ayudarle a entender qué hacen ' +
  'los servicios digitales con sus datos personales. Como un sistema que promueve la privacidad debe ' +
  'ser el primero en respetarla, este aviso le explica con claridad qué datos trata PrivApp, para qué ' +
  'y cómo puede controlarlos.'

const ENLACE_OPENAI: Enlace = {
  texto: 'Controles de datos de la plataforma de OpenAI',
  url: 'https://developers.openai.com/api/docs/guides/your-data',
}

export const SECCIONES_AVISO: SeccionAviso[] = [
  {
    id: 'responsable',
    titulo: '1. ¿Quién es responsable de sus datos?',
    bloques: [
      {
        tipo: 'parrafo',
        texto:
          'PrivApp es un proyecto de graduación desarrollado por Jairo Ardani Castillo Girón, estudiante ' +
          'de Ingeniería en Sistemas de Información y Ciencias de la Computación de la Universidad ' +
          'Mariano Gálvez de Guatemala, Campus Jutiapa. Para cualquier consulta sobre sus datos puede ' +
          `escribir a ${CORREO_CONTACTO}.`,
      },
    ],
  },
  {
    id: 'datos-que-tratamos',
    titulo: '2. ¿Qué datos tratamos?',
    bloques: [
      {
        tipo: 'parrafo',
        etiqueta: 'Datos de su cuenta.',
        texto:
          'Al registrarse, guardamos su nombre, su correo electrónico y su contraseña. La contraseña ' +
          'nunca se guarda tal como usted la escribe: se almacena cifrada, de modo que ni siquiera el ' +
          'administrador puede conocerla. También guardamos su rol dentro del sistema, si su cuenta está ' +
          'activa o desactivada, la fecha en que se registró, la fecha en que aceptó este aviso y la ' +
          'fecha en que declaró ser mayor de 18 años o contar con el consentimiento de su madre, padre o ' +
          'persona encargada.',
      },
      {
        tipo: 'parrafo',
        etiqueta: 'Datos de sus análisis.',
        texto:
          'Cuando analiza una política de privacidad, guardamos los primeros 2,000 caracteres de su ' +
          'texto, el resultado del análisis, la fecha en que lo realizó y el tiempo que tardó en ' +
          'generarse cada reporte.',
      },
      {
        tipo: 'parrafo',
        etiqueta: 'Datos técnicos.',
        texto:
          'Para mantener su sesión abierta, su navegador guarda un código de acceso temporal en su ' +
          'almacenamiento local, que vence a las 24 horas. Al cerrar sesión, el identificador de ese ' +
          'código se registra temporalmente para impedir que vuelva a usarse, hasta que venza. Su ' +
          'dirección IP se utiliza solo para limitar el número de solicitudes y proteger el sistema ' +
          'contra abusos: se conserva en la memoria del servidor como máximo un minuto y no se escribe ' +
          'en los registros técnicos.',
      },
    ],
  },
  {
    id: 'datos-que-no-guardamos',
    titulo: '3. ¿Qué datos no guardamos ni recopilamos?',
    bloques: [
      {
        tipo: 'lista',
        elementos: [
          {
            texto:
              'No guardamos el texto completo de las políticas que analiza: se procesa en la memoria ' +
              'del servidor durante el análisis y solo se conservan sus primeros 2,000 caracteres.',
          },
          {
            texto:
              'No guardamos los archivos PDF o de texto que carga: se leen para extraer su texto y se ' +
              'descartan de inmediato.',
          },
          {
            texto:
              'No usamos cookies, herramientas de analítica, publicidad ni servicios de terceros en su ' +
              'navegador.',
          },
          { texto: 'No vendemos ni cedemos sus datos a nadie con fines comerciales.' },
        ],
      },
    ],
  },
  {
    id: 'finalidades',
    titulo: '4. ¿Para qué usamos sus datos?',
    bloques: [
      { tipo: 'parrafo', texto: 'Usamos sus datos únicamente para:' },
      {
        tipo: 'lista',
        elementos: [
          { texto: 'crear y proteger su cuenta, y permitirle iniciar sesión;' },
          { texto: 'analizar las políticas de privacidad que usted envía y mostrarle sus resultados;' },
          { texto: 'conservar su historial de análisis para que pueda consultarlo, descargarlo o eliminarlo;' },
          { texto: 'proteger el sistema contra usos indebidos;' },
          {
            texto:
              'evaluar el funcionamiento del sistema como parte de un proyecto académico, sin ' +
              'identificar a ninguna persona en los resultados.',
          },
        ],
      },
    ],
  },
  {
    id: 'terceros',
    titulo: '5. ¿Con quién compartimos información?',
    bloques: [
      {
        tipo: 'lista',
        elementos: [
          {
            etiqueta: 'OpenAI (Estados Unidos).',
            texto:
              'Para analizar una política, PrivApp envía su texto, dividido en secciones, al servicio ' +
              'de inteligencia artificial de OpenAI. No se envían su nombre, su correo ni ningún otro ' +
              'dato de su cuenta. Según las condiciones de OpenAI para su plataforma, la información ' +
              'que recibe por este medio no se usa para entrenar sus modelos y puede conservarse hasta ' +
              '30 días para detectar usos indebidos, salvo que la ley exija conservarla por más tiempo. ' +
              'El tratamiento que OpenAI hace de esa información se rige por sus propias condiciones de ' +
              'uso. Por esta razón, le pedimos no incluir datos personales en los textos que analiza.',
            enlace: ENLACE_OPENAI,
          },
          {
            etiqueta: 'Railway.',
            texto:
              'PrivApp se aloja en la plataforma Railway, [región del servidor], que por su ' +
              'funcionamiento recibe su dirección IP al conectarse.',
          },
          {
            etiqueta: 'Páginas web consultadas.',
            texto:
              'Si analiza una política indicando su dirección web, el servidor de PrivApp descarga esa ' +
              'página por usted; el sitio consultado ve la dirección del servidor, no la suya. En los ' +
              'registros técnicos del servidor queda solo el nombre del sitio consultado (por ejemplo, ' +
              'www.ejemplo.com), no la dirección completa ni quién la consultó.',
          },
        ],
      },
    ],
  },
  {
    id: 'conservacion',
    titulo: '6. ¿Cuánto tiempo conservamos sus datos?',
    bloques: [
      {
        tipo: 'tabla',
        encabezados: ['Dato', 'Tiempo de conservación'],
        filas: [
          ['Datos de su cuenta', 'Mientras su cuenta exista'],
          ['Análisis y sus resultados', 'Hasta que usted los elimine; no se eliminan automáticamente'],
          ['Código de acceso de su sesión', '24 horas como máximo'],
          ['Registro de cierre de sesión', 'Hasta que vence el código correspondiente, como máximo 24 horas'],
          ['Dirección IP', 'Como máximo un minuto, en la memoria del servidor'],
          ['Texto enviado a OpenAI', 'Hasta 30 días en OpenAI, según sus condiciones'],
          [
            'Nombre de los sitios consultados (registros técnicos)',
            '[tiempo de conservación de los registros del servidor]',
          ],
        ],
      },
    ],
  },
  {
    id: 'proteccion',
    titulo: '7. ¿Cómo protegemos sus datos?',
    bloques: [
      {
        tipo: 'lista',
        elementos: [
          { texto: 'Las contraseñas se almacenan cifradas.' },
          { texto: 'La comunicación con el sistema viaja protegida mediante conexión segura (HTTPS).' },
          {
            texto:
              'Solo usted puede ver sus análisis. El administrador del sistema puede ver su nombre, ' +
              'correo, rol, estado y fecha de registro, pero no el contenido de sus análisis.',
          },
          {
            texto:
              'Las sesiones pueden invalidarse al cerrar sesión, al cambiar la contraseña o al ' +
              'desactivar una cuenta.',
          },
          {
            texto:
              'Los registros técnicos del servidor no guardan su correo, su dirección IP, los nombres ' +
              'de los archivos que carga ni las direcciones web completas que consulta.',
          },
        ],
      },
    ],
  },
  {
    id: 'derechos',
    titulo: '8. ¿Qué puede hacer con sus datos?',
    bloques: [
      {
        tipo: 'lista',
        elementos: [
          {
            etiqueta: 'Consultarlos:',
            texto: 'puede ver los datos de su cuenta en su perfil y todos sus análisis en su historial.',
          },
          {
            etiqueta: 'Corregirlos:',
            texto: `puede modificar su nombre desde su perfil. Para corregir su correo, escriba a ${CORREO_CONTACTO}.`,
          },
          {
            etiqueta: 'Eliminar sus análisis:',
            texto: 'puede eliminar cualquier análisis desde su historial; la eliminación es definitiva.',
          },
          {
            etiqueta: 'Eliminar su cuenta:',
            texto:
              'puede eliminarla usted mismo desde su perfil, confirmando con su contraseña. Al ' +
              'eliminarse su cuenta, se eliminan también todos sus análisis; la eliminación es definitiva.',
          },
          { etiqueta: 'Cambiar su contraseña:', texto: 'desde su perfil, en cualquier momento.' },
        ],
      },
    ],
  },
  {
    id: 'menores',
    titulo: '9. Personas menores de edad',
    bloques: [
      {
        tipo: 'parrafo',
        texto:
          'PrivApp está pensado para jóvenes, incluidos adolescentes. Si usted es menor de 18 años, ' +
          'necesita el consentimiento de su madre, padre o persona encargada para usar PrivApp: al ' +
          'registrarse se le pide declarar que es mayor de edad o que cuenta con ese consentimiento. Le ' +
          'recomendamos leer este aviso junto con ellos antes de registrarse.',
      },
    ],
  },
  {
    id: 'marco-de-referencia',
    titulo: '10. Marco de referencia',
    bloques: [
      {
        tipo: 'parrafo',
        texto:
          'Guatemala no cuenta actualmente con una ley integral de protección de datos personales. Por ' +
          'ello, PrivApp adopta de forma voluntaria principios reconocidos en marcos internacionales de ' +
          'referencia, como la recopilación mínima de datos, el uso limitado a fines declarados, la ' +
          'transparencia y el control del usuario sobre su información, sin que ello implique que dichos ' +
          'marcos sean de aplicación obligatoria en el país.',
      },
    ],
  },
  {
    id: 'cambios',
    titulo: '11. Cambios a este aviso',
    bloques: [
      {
        tipo: 'parrafo',
        texto:
          'Si este aviso cambia, publicaremos la nueva versión en esta misma página con su fecha de ' +
          'actualización.',
      },
    ],
  },
  {
    id: 'contacto',
    titulo: '12. Contacto',
    bloques: [
      {
        tipo: 'parrafo',
        texto: `Para cualquier duda, solicitud o comentario sobre sus datos: ${CORREO_CONTACTO}.`,
      },
    ],
  },
]

/** Datos entre corchetes que faltan por completar, sin repetir. */
export function datosPendientes(secciones: SeccionAviso[] = SECCIONES_AVISO): string[] {
  const textos = [ULTIMA_ACTUALIZACION, INTRODUCCION]
  for (const seccion of secciones) {
    for (const bloque of seccion.bloques) {
      if (bloque.tipo === 'parrafo') textos.push(bloque.texto)
      else if (bloque.tipo === 'lista') textos.push(...bloque.elementos.map((e) => e.texto))
      else textos.push(...bloque.filas.flat())
    }
  }
  return [...new Set(textos.flatMap((t) => t.match(/\[[^\]]+\]/g) ?? []))]
}
