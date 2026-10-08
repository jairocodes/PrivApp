#!/usr/bin/env python3
"""Promueve a un usuario registrado al rol de administrador.

Uso:
    docker compose exec backend python scripts/promover_admin.py correo@ejemplo.com

Es la única forma de asignar el rol administrador: ninguna ruta de la API
permite elevar roles. El usuario debe iniciar sesión de nuevo para que su
token refleje el rol (el servidor ya lo reconoce desde el momento del cambio).
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Necesario para que Python encuentre el paquete `app` desde scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.exceptions import UsuarioNoEncontradoError
from app.database import AsyncSessionLocal
from app.services.auth_service import promover_a_administrador


async def main(email: str) -> int:
    async with AsyncSessionLocal() as db:
        try:
            user = await promover_a_administrador(db, email)
        except UsuarioNoEncontradoError:
            print(f"No existe un usuario registrado con el correo {email}.", file=sys.stderr)
            return 1
        await db.commit()
        print(f"Usuario {user.email} (id={user.id}) promovido a administrador.")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("email", help="Correo del usuario a promover")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.email)))
