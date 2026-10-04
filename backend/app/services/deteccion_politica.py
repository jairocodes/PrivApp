"""Detección de si un texto es una política de privacidad (o un documento que
explica el tratamiento de datos personales), antes de analizarlo.

Combina tres señales deterministas, sin llamar al modelo de lenguaje:

1. Vocabulario: cuántos de los temas típicos de una política aparecen en el
   texto (datos personales, finalidad, terceros, conservación, derechos...).
2. Semejanza semántica: qué parte del texto se parece, según el modelo de
   embeddings del corpus, a cláusulas típicas de una política.
3. Voz del responsable: una política describe sus propias prácticas
   ("recopilamos", "compartimos", "la empresa utilizará"); un texto que solo
   habla sobre la privacidad (un artículo, una tarea) no lo hace.

El resultado es "politica", "dudosa" o "no_politica"; los umbrales se
calibraron con scripts/evaluar_deteccion.py.
"""

import re
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache

from app.utils import embeddings

# Temas típicos de una política de privacidad. Cada tema se cuenta una vez si
# aparece cualquiera de sus expresiones (texto en minúsculas y sin tildes).
TEMAS: dict[str, tuple[str, ...]] = {
    "datos personales": (
        "datos personales", "informacion personal", "datos de caracter personal", "tus datos",
        "sus datos", "personal data", "personal information", "your data", "your information",
    ),
    "privacidad": (
        "politica de privacidad", "aviso de privacidad", "declaracion de privacidad", "proteccion de datos",
        "privacy policy", "privacy notice", "privacy statement", "data protection",
    ),
    "finalidad": (
        "finalidad", "finalidades", "para que usamos", "como usamos", "como utilizamos", "utilizamos tu",
        "utilizamos sus", "usamos tu", "usamos sus", "purposes", "how we use", "we use your",
    ),
    "terceros": (
        "terceros", "compartimos", "compartir tus", "compartir sus", "socios", "proveedores de servicios",
        "third parties", "third-party", "we share", "service providers",
    ),
    "conservacion": (
        "conservamos", "conservacion", "conservar", "retencion", "plazo", "periodo de tiempo",
        "retain", "retention", "how long",
    ),
    "derechos": (
        "derecho de acceso", "derechos de acceso", "rectificacion", "supresion", "cancelacion", "oposicion",
        "portabilidad", "tus derechos", "sus derechos", "your rights", "right to access", "right to delete",
    ),
    "cookies": ("cookies", "cookie", "tecnologias similares", "web beacons", "pixeles", "similar technologies"),
    "seguridad": (
        "medidas de seguridad", "proteger tu informacion", "proteger sus datos", "acceso no autorizado",
        "security measures", "unauthorized access",
    ),
    "contacto": (
        "responsable del tratamiento", "delegado de proteccion", "contactanos", "contacta con nosotros",
        "ponte en contacto", "data protection officer", "contact us", "controller",
    ),
    "cambios": (
        "cambios en esta politica", "cambios a esta politica", "actualizar esta politica", "modificar esta politica",
        "actualizaremos", "changes to this", "update this policy", "updates to this",
    ),
}

# Expresiones con las que el responsable describe sus prácticas, en primera
# persona o en tercera (políticas que hablan de "la empresa").
_VOZ_RESPONSABLE = re.compile(
    r"\b(?:"
    r"recopilamos|recogemos|obtenemos|recibimos|utilizamos|usamos|compartimos|conservamos|almacenamos|"
    r"tratamos|procesamos|divulgamos|transferimos|nuestros servicios|nuestro servicio|nuestra plataforma|"
    r"nuestras aplicaciones|nuestro sitio|we collect|we use|we share|we store|we process|we receive|our services|"
    r"(?:la empresa|la compania|la plataforma|el responsable|el prestador) "
    r"(?:recopila|recopilara|recoge|utiliza|utilizara|usa|usara|comparte|compartira|trata|tratara|"
    r"conserva|conservara|almacena|almacenara|podra compartir|podra utilizar)"
    r")\b"
)

# Cláusulas típicas con las que se compara cada fragmento del texto. Son frases
# de calibración internas (no se muestran a nadie).
PROTOTIPOS: tuple[str, ...] = (
    "Recopilamos tus datos personales, como tu nombre, correo electrónico y número de teléfono, cuando creas una cuenta.",
    "Utilizamos tu información para prestar el servicio, personalizar el contenido y mostrarte publicidad.",
    "Podemos compartir tus datos con proveedores de servicios, socios comerciales y autoridades cuando la ley lo exija.",
    "Conservamos tus datos durante el tiempo necesario para cumplir las finalidades descritas en esta política.",
    "Puedes ejercer tus derechos de acceso, rectificación, supresión y oposición escribiendo a nuestro equipo de privacidad.",
    "Utilizamos cookies y tecnologías similares para recordar tus preferencias y analizar el uso del sitio.",
    "Aplicamos medidas de seguridad técnicas y organizativas para proteger tu información frente a accesos no autorizados.",
    "Podemos actualizar esta política de privacidad y te notificaremos los cambios importantes.",
    "Nuestros servicios no están dirigidos a menores de edad sin el consentimiento de sus padres o tutores.",
    "Tus datos pueden transferirse y almacenarse en servidores ubicados en otros países.",
    "Recibimos información sobre tu dispositivo, tu dirección IP y tu ubicación aproximada cuando usas la aplicación.",
    "El responsable del tratamiento de tus datos personales es la empresa que presta el servicio.",
)

# Fragmentos del texto que se comparan (ventanas de palabras), como máximo.
_PALABRAS_POR_FRAGMENTO = 80
_MAX_FRAGMENTOS = 40
# Semejanza a partir de la cual un fragmento "parece" una cláusula de política.
UMBRAL_FRAGMENTO = 0.45

# Umbrales de la decisión (calibrados con scripts/evaluar_deteccion.py).
TEMAS_POLITICA = 5
COBERTURA_POLITICA = 0.30
VOZ_POLITICA = 3
TEMAS_NO_POLITICA = 2
COBERTURA_NO_POLITICA = 0.25


@dataclass(frozen=True)
class Deteccion:
    resultado: str  # "politica" | "dudosa" | "no_politica"
    temas_encontrados: list[str]
    temas_total: int
    cobertura: float  # fracción de fragmentos que se parecen a una cláusula de política
    voz_responsable: int  # expresiones con las que el responsable describe sus prácticas

    def como_dict(self) -> dict:
        return asdict(self)


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_tildes)


def temas_presentes(texto: str) -> list[str]:
    normal = normalizar(texto)
    return [tema for tema, expresiones in TEMAS.items() if any(e in normal for e in expresiones)]


def expresiones_responsable(texto: str) -> int:
    return len(_VOZ_RESPONSABLE.findall(normalizar(texto)))


def _fragmentos(texto: str) -> list[str]:
    palabras = texto.split()
    ventanas = [
        " ".join(palabras[i : i + _PALABRAS_POR_FRAGMENTO])
        for i in range(0, len(palabras), _PALABRAS_POR_FRAGMENTO)
    ]
    ventanas = [v for v in ventanas if len(v.split()) >= 15] or ventanas
    if len(ventanas) <= _MAX_FRAGMENTOS:
        return ventanas
    # Muestra repartida por todo el documento (siempre la misma para el mismo texto).
    paso = len(ventanas) / _MAX_FRAGMENTOS
    return [ventanas[int(i * paso)] for i in range(_MAX_FRAGMENTOS)]


_vectores_prototipos: list[list[float]] | None = None


def cobertura_semantica(texto: str) -> float:
    """Fracción de fragmentos del texto cuya semejanza con alguna cláusula
    típica de una política supera UMBRAL_FRAGMENTO."""
    global _vectores_prototipos
    fragmentos = _fragmentos(texto)
    if not fragmentos:
        return 0.0
    if _vectores_prototipos is None:
        _vectores_prototipos = embeddings.encode_batch(list(PROTOTIPOS))
    vectores = embeddings.encode_batch(fragmentos)
    # Vectores normalizados: el producto punto es la semejanza coseno.
    cercanos = sum(
        1 for v in vectores
        if max(sum(a * b for a, b in zip(v, p)) for p in _vectores_prototipos) >= UMBRAL_FRAGMENTO
    )
    return round(cercanos / len(vectores), 3)


def decidir(temas: int, cobertura: float, voz: int) -> str:
    """Sin voz del responsable el texto nunca pasa solo (queda dudoso), pero
    tampoco se rechaza por eso: hay políticas redactadas de forma impersonal."""
    if temas >= TEMAS_POLITICA and cobertura >= COBERTURA_POLITICA and voz >= VOZ_POLITICA:
        return "politica"
    if temas <= TEMAS_NO_POLITICA and cobertura < COBERTURA_NO_POLITICA:
        return "no_politica"
    return "dudosa"


# La ingesta y el inicio del análisis evalúan el mismo texto: se recuerda el
# resultado de los últimos textos para no calcular los embeddings dos veces.
@lru_cache(maxsize=16)
def detectar_politica(texto: str) -> Deteccion:
    """Clasifica el texto. Es una operación de CPU (embeddings): desde código
    asíncrono, llamarla en un hilo aparte."""
    temas = temas_presentes(texto)
    cobertura = cobertura_semantica(texto)
    voz = expresiones_responsable(texto)
    return Deteccion(
        resultado=decidir(len(temas), cobertura, voz),
        temas_encontrados=temas,
        temas_total=len(TEMAS),
        cobertura=cobertura,
        voz_responsable=voz,
    )
