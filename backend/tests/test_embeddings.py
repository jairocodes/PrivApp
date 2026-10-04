"""Carga del modelo de embeddings desde la caché local."""

from app.utils.embeddings import MODEL_NAME, ruta_modelo_local


def _snapshot(base, nombre, completo=True):
    carpeta = base / f"models--sentence-transformers--{MODEL_NAME}" / "snapshots" / nombre
    carpeta.mkdir(parents=True)
    if completo:
        (carpeta / "modules.json").write_text("[]")
    return carpeta


def test_sin_descargar_no_hay_ruta_local(tmp_path):
    assert ruta_modelo_local(tmp_path) is None


def test_usa_la_carpeta_descargada(tmp_path):
    carpeta = _snapshot(tmp_path, "abc123")
    assert ruta_modelo_local(tmp_path) == carpeta


def test_ignora_una_descarga_incompleta(tmp_path):
    _snapshot(tmp_path, "incompleta", completo=False)
    assert ruta_modelo_local(tmp_path) is None
