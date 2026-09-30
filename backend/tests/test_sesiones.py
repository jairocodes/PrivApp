"""Tests de la invalidación de todas las sesiones de un usuario."""

import time

from app.core.security import create_access_token, decode_access_token


# ---------------------------------------------------------------------------
# Fecha de emisión del token
# ---------------------------------------------------------------------------

class TestFechaDeEmision:
    def test_token_incluye_iat_con_fraccion_de_segundo(self):
        antes = time.time()
        payload = decode_access_token(create_access_token("1"))
        despues = time.time()

        assert antes <= payload["iat"] <= despues
        assert isinstance(payload["iat"], float)
