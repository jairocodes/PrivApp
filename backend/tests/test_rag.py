"""Tests del corpus normativo y arquitectura RAG.

Las pruebas de embeddings y RAG mockean el modelo y la base de datos
para evitar cargar el modelo de 450 MB en el entorno de CI.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Chunking — función pura, sin dependencias externas
# ---------------------------------------------------------------------------

class TestChunking:
    def test_texto_corto_produce_un_chunk(self):
        from app.utils.chunking import chunk_texto

        texto = "Esta es una prueba de texto. " * 30  # ~150 palabras
        chunks = chunk_texto(texto)
        assert len(chunks) == 1

    def test_texto_largo_produce_multiples_chunks(self):
        from app.utils.chunking import chunk_texto

        parrafo = "Esta es una palabra de prueba " * 30  # ~150 palabras
        texto = "\n\n".join([parrafo] * 6)  # ~900 palabras
        chunks = chunk_texto(texto)
        assert len(chunks) >= 2

    def test_texto_muy_corto_no_produce_chunks(self):
        from app.utils.chunking import chunk_texto

        chunks = chunk_texto("Hola mundo")
        assert chunks == []

    def test_texto_vacio_devuelve_lista_vacia(self):
        from app.utils.chunking import chunk_texto

        assert chunk_texto("") == []
        assert chunk_texto("   \n\n  ") == []

    def test_cada_chunk_tiene_contenido_minimo(self):
        from app.utils.chunking import chunk_texto, MIN_CHUNK_WORDS

        texto = "palabra " * 500
        chunks = chunk_texto(texto)
        for chunk in chunks:
            assert len(chunk.split()) >= MIN_CHUNK_WORDS

    def test_solapamiento_entre_chunks(self):
        from app.utils.chunking import chunk_texto, OVERLAP_WORDS

        # Dos párrafos bien diferenciados de ~300 palabras cada uno
        p1 = "alfa " * 300
        p2 = "beta " * 300
        texto = p1 + "\n\n" + p2
        chunks = chunk_texto(texto)

        assert len(chunks) >= 2
        # El segundo chunk debe contener palabras del primero (solapamiento)
        palabras_chunk2 = chunks[1].split()
        assert "alfa" in palabras_chunk2, "El solapamiento debería incluir palabras del chunk anterior"

    def test_parrafo_gigante_se_divide(self):
        from app.utils.chunking import chunk_texto

        # Un único párrafo de 1000 palabras (sin saltos de línea)
        texto = "enorme " * 1000
        chunks = chunk_texto(texto)
        assert len(chunks) >= 2


# ---------------------------------------------------------------------------
# Metadatos del corpus — funciones puras del script de carga
# ---------------------------------------------------------------------------

class TestMetadatosCorpus:
    def test_inferir_jurisdiccion_guatemala(self):
        from scripts.cargar_corpus import inferir_jurisdiccion

        ruta = Path("corpus_normativo/guatemala/constitucion.pdf")
        assert inferir_jurisdiccion(ruta) == "guatemala"

    def test_inferir_jurisdiccion_internacional(self):
        from scripts.cargar_corpus import inferir_jurisdiccion

        ruta = Path("corpus_normativo/internacional/rgpd.pdf")
        assert inferir_jurisdiccion(ruta) == "internacional"

    def test_inferir_jurisdiccion_estandar(self):
        from scripts.cargar_corpus import inferir_jurisdiccion

        ruta = Path("corpus_normativo/estandares_tecnicos/opp_115.pdf")
        assert inferir_jurisdiccion(ruta) == "estandar_tecnico"

    def test_inferir_jurisdiccion_desconocida(self):
        from scripts.cargar_corpus import inferir_jurisdiccion

        ruta = Path("otro_directorio/archivo.pdf")
        assert inferir_jurisdiccion(ruta) == "desconocido"

    def test_inferir_categoria_constitucion(self):
        from scripts.cargar_corpus import inferir_categoria

        assert inferir_categoria("constitucion_politica") == "derechos_fundamentales"

    def test_inferir_categoria_rgpd(self):
        from scripts.cargar_corpus import inferir_categoria

        assert inferir_categoria("rgpd_articulos_clave") == "proteccion_datos"

    def test_inferir_categoria_laip(self):
        from scripts.cargar_corpus import inferir_categoria

        assert inferir_categoria("decreto_57_2008_laip") == "acceso_informacion"

    def test_inferir_categoria_opp(self):
        from scripts.cargar_corpus import inferir_categoria

        assert inferir_categoria("opp_115_taxonomia") == "taxonomia_privacidad"

    def test_hash_chunk_deterministico(self):
        from scripts.cargar_corpus import hash_chunk

        h1 = hash_chunk("doc.pdf", "texto de prueba")
        h2 = hash_chunk("doc.pdf", "texto de prueba")
        assert h1 == h2

    def test_hash_chunk_diferente_contenido(self):
        from scripts.cargar_corpus import hash_chunk

        h1 = hash_chunk("doc.pdf", "texto A")
        h2 = hash_chunk("doc.pdf", "texto B")
        assert h1 != h2


# ---------------------------------------------------------------------------
# Extractor de PDF — verifica manejo de archivos inexistentes
# ---------------------------------------------------------------------------

class TestArchivosDelCorpus:
    def test_solo_incluye_archivos_de_las_carpetas_de_jurisdiccion(self, tmp_path):
        from scripts.cargar_corpus import archivos_del_corpus

        for ruta in [
            "README.md",
            "notas/borrador.md",
            "guatemala/Constitucion.pdf",
            "internacional/RGPD.pdf",
            "estandares_tecnicos/tosdr_metodologia.md",
            "estandares_tecnicos/README.md.bak",
            "internacional/imagen.png",
        ]:
            archivo = tmp_path / ruta
            archivo.parent.mkdir(parents=True, exist_ok=True)
            archivo.write_text("contenido")

        incluidos = [p.relative_to(tmp_path).as_posix() for p in archivos_del_corpus(tmp_path)]

        assert incluidos == [
            "estandares_tecnicos/tosdr_metodologia.md",
            "guatemala/Constitucion.pdf",
            "internacional/RGPD.pdf",
        ]

    def test_el_corpus_real_no_incluye_su_readme(self):
        from scripts.cargar_corpus import CORPUS_DIR, archivos_del_corpus

        if not CORPUS_DIR.exists() or not any(CORPUS_DIR.iterdir()):
            pytest.skip("corpus_normativo no está montado en este entorno")
        nombres = [p.name for p in archivos_del_corpus(CORPUS_DIR)]
        assert "README.md" not in nombres
        assert "tosdr_metodologia.md" in nombres


class TestConsultaDeRecuperacion:
    """La consulta real se prueba contra PostgreSQL en tests/integracion."""

    async def test_solo_considera_fragmentos_activos_y_ordena_por_distancia(self):
        from app.repositories.corpus import RepositorioCorpusNormativo

        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(mappings=MagicMock(return_value=MagicMock(all=list))))

        await RepositorioCorpusNormativo(db).buscar_similares("[0.1]", k=5, filtro_jurisdiccion="guatemala")

        consulta = str(db.execute.call_args_list[-1].args[0])
        assert "active = true" in consulta
        assert "jurisdiccion = :jurisdiccion" in consulta
        assert "ORDER  BY embedding <=>" in consulta


class TestPdfExtractor:
    def test_archivo_inexistente_devuelve_vacio(self):
        from app.utils.pdf_extractor import extraer_texto_pdf

        resultado = extraer_texto_pdf(Path("/ruta/que/no/existe.pdf"))
        assert resultado == ""

    def test_extraccion_con_pdfplumber_mock(self, tmp_path):
        """Verifica el flujo sin necesitar un PDF real."""
        from app.utils.pdf_extractor import _extraer_con_pdfplumber

        pagina_mock = MagicMock()
        pagina_mock.extract_text.return_value = "Texto de la página uno."

        pdf_mock = MagicMock()
        pdf_mock.__enter__ = MagicMock(return_value=pdf_mock)
        pdf_mock.__exit__ = MagicMock(return_value=False)
        pdf_mock.pages = [pagina_mock]

        archivo_dummy = tmp_path / "test.pdf"
        archivo_dummy.write_bytes(b"dummy")

        with patch("pdfplumber.open", return_value=pdf_mock):
            resultado = _extraer_con_pdfplumber(archivo_dummy)

        assert "Texto de la página uno" in resultado


class TestPdfExtractorEnMemoria:
    """Extracción desde bytes con PDF reales generados con ReportLab."""

    def test_extrae_el_texto_de_un_pdf_real(self):
        from app.utils.pdf_extractor import extraer_texto_pdf_bytes
        from tests.pdf_de_prueba import LINEAS_POLITICA, pdf_con_texto

        texto = extraer_texto_pdf_bytes(pdf_con_texto(LINEAS_POLITICA), "politica.pdf")

        assert "Recopilamos su nombre" in texto
        assert "eliminacion de sus datos" in texto

    def test_pdf_de_varias_paginas(self):
        from app.utils.pdf_extractor import extraer_texto_pdf_bytes
        from tests.pdf_de_prueba import pdf_con_texto

        lineas = [f"Linea numero {i} de la politica." for i in range(120)]
        texto = extraer_texto_pdf_bytes(pdf_con_texto(lineas))

        assert "Linea numero 0 " in texto
        assert "Linea numero 119 " in texto

    def test_pdf_sin_texto_devuelve_vacio(self):
        from app.utils.pdf_extractor import extraer_texto_pdf_bytes
        from tests.pdf_de_prueba import pdf_sin_texto

        assert extraer_texto_pdf_bytes(pdf_sin_texto()) == ""

    def test_contenido_que_no_es_pdf_devuelve_vacio(self):
        from app.utils.pdf_extractor import extraer_texto_pdf_bytes

        assert extraer_texto_pdf_bytes(b"%PDF-1.4 esto no es un PDF valido") == ""

    def test_si_pdfplumber_falla_usa_pypdf(self):
        from app.utils.pdf_extractor import extraer_texto_pdf_bytes
        from tests.pdf_de_prueba import LINEAS_POLITICA, pdf_con_texto

        with patch("pdfplumber.open", side_effect=RuntimeError("fallo simulado")):
            texto = extraer_texto_pdf_bytes(pdf_con_texto(LINEAS_POLITICA))

        assert "Recopilamos su nombre" in texto

    def test_extrae_desde_disco_como_el_script_del_corpus(self, tmp_path):
        from app.utils.pdf_extractor import extraer_texto_pdf
        from tests.pdf_de_prueba import LINEAS_POLITICA, pdf_con_texto

        ruta = tmp_path / "norma.pdf"
        ruta.write_bytes(pdf_con_texto(LINEAS_POLITICA))

        assert "Conservamos la informacion" in extraer_texto_pdf(ruta)


# ---------------------------------------------------------------------------
# Embeddings — no carga el modelo real
# ---------------------------------------------------------------------------

class TestEmbeddings:
    def test_encode_devuelve_lista_de_floats(self):
        from app.utils.embeddings import encode

        vector_mock = MagicMock()
        vector_mock.tolist.return_value = [0.1] * 768

        with patch("app.utils.embeddings.get_model") as mock_get:
            mock_modelo = MagicMock()
            mock_modelo.encode.return_value = vector_mock
            mock_get.return_value = mock_modelo

            resultado = encode("texto de prueba")

        assert isinstance(resultado, list)
        assert len(resultado) == 768

    def test_encode_batch_devuelve_lista_de_vectores(self):
        from app.utils.embeddings import encode_batch

        vector_mock = MagicMock()
        vector_mock.tolist.return_value = [0.1] * 768

        with patch("app.utils.embeddings.get_model") as mock_get:
            mock_modelo = MagicMock()
            mock_modelo.encode.return_value = [vector_mock, vector_mock]
            mock_get.return_value = mock_modelo

            resultado = encode_batch(["texto 1", "texto 2"])

        assert len(resultado) == 2

    def test_encode_batch_lista_vacia(self):
        from app.utils.embeddings import encode_batch

        resultado = encode_batch([])
        assert resultado == []


# ---------------------------------------------------------------------------
# RAG Service — mock de DB y embeddings
# ---------------------------------------------------------------------------

class TestRAGService:
    async def test_recuperar_contexto_devuelve_lista(self):
        from app.services.rag_service import recuperar_contexto

        fila_mock = {
            "id": 1,
            "documento_fuente": "rgpd.pdf",
            "jurisdiccion": "internacional",
            "referencia": "Artículo 5 RGPD",
            "categoria_tematica": "proteccion_datos",
            "texto_original": "Los datos personales deben ser tratados de forma lícita.",
            "metadatos": {"hash": "abc123"},
        }

        result_mock = MagicMock()
        result_mock.mappings.return_value.all.return_value = [fila_mock]

        db_mock = AsyncMock()
        db_mock.execute.return_value = result_mock

        embedding_mock = [0.1] * 768

        with patch("app.services.rag_service.encode", return_value=embedding_mock):
            chunks = await recuperar_contexto(db_mock, "tratamiento de datos personales")

        assert len(chunks) == 1
        assert chunks[0].jurisdiccion == "internacional"
        assert chunks[0].referencia == "Artículo 5 RGPD"

    async def test_recuperar_contexto_corpus_vacio(self):
        from app.services.rag_service import recuperar_contexto

        result_mock = MagicMock()
        result_mock.mappings.return_value.all.return_value = []

        db_mock = AsyncMock()
        db_mock.execute.return_value = result_mock

        with patch("app.services.rag_service.encode", return_value=[0.0] * 768):
            chunks = await recuperar_contexto(db_mock, "texto sin resultados")

        assert chunks == []

    async def test_recuperar_contexto_aplica_filtro_jurisdiccion(self):
        from app.services.rag_service import recuperar_contexto

        result_mock = MagicMock()
        result_mock.mappings.return_value.all.return_value = []

        db_mock = AsyncMock()
        db_mock.execute.return_value = result_mock

        with patch("app.services.rag_service.encode", return_value=[0.0] * 768):
            await recuperar_contexto(
                db_mock, "texto", filtro_jurisdiccion="guatemala"
            )

        call_args = db_mock.execute.call_args
        sql_str = str(call_args[0][0])
        assert "jurisdiccion" in sql_str

    @staticmethod
    def _fila(id_, jurisdiccion):
        return {
            "id": id_, "documento_fuente": f"doc{id_}.pdf", "jurisdiccion": jurisdiccion,
            "referencia": None, "categoria_tematica": "general",
            "texto_original": "texto", "metadatos": {},
        }

    async def test_agrega_fragmentos_guatemaltecos_sin_repetir(self):
        from app.services.rag_service import recuperar_contexto

        cercanos = [self._fila(1, "internacional"), self._fila(2, "guatemala"), self._fila(3, "internacional")]
        guatemala = [self._fila(2, "guatemala"), self._fila(7, "guatemala")]

        with patch("app.services.rag_service.encode", return_value=[0.0] * 768), \
             patch("app.services.rag_service.RepositorioCorpusNormativo") as Repo:
            Repo.return_value.buscar_similares = AsyncMock(side_effect=[cercanos, guatemala])
            chunks = await recuperar_contexto(AsyncMock(), "texto", k=3, k_guatemala=2)

        assert [c.id for c in chunks] == [1, 2, 3, 7]
        segunda = Repo.return_value.buscar_similares.call_args_list[1]
        assert segunda.args[1:3] == (2, "guatemala")

    async def test_sin_k_guatemala_hace_una_sola_busqueda(self):
        from app.services.rag_service import recuperar_contexto

        with patch("app.services.rag_service.encode", return_value=[0.0] * 768), \
             patch("app.services.rag_service.RepositorioCorpusNormativo") as Repo:
            Repo.return_value.buscar_similares = AsyncMock(return_value=[self._fila(1, "internacional")])
            chunks = await recuperar_contexto(AsyncMock(), "texto", k=5)

        assert len(chunks) == 1
        assert Repo.return_value.buscar_similares.await_count == 1

    async def test_contar_chunks(self):
        from app.services.rag_service import contar_chunks

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 42

        db_mock = AsyncMock()
        db_mock.execute.return_value = result_mock

        total = await contar_chunks(db_mock)
        assert total == 42
