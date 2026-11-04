"""Seguridad de la app: por ahora sólo el hash ficticio del login.

CHG-10 completa este módulo (hash y verificación de contraseñas, semáforo de
bcrypt y JWT) sin cambiar la firma de `calcular_hash_ficticio`.
"""
import secrets

import bcrypt


def calcular_hash_ficticio(costo: int) -> str:
    """Hash bcrypt de una contraseña aleatoria que se descarta (nadie la conoce).

    El login lo verifica cuando el correo no existe, para que tarde lo mismo que con
    un correo real (RN-08): por eso usa el MISMO costo que los hashes reales.
    Es síncrona y bloquea (~300 ms con costo 12): el lifespan la llama con
    `asyncio.to_thread`.
    """
    # token_urlsafe(32) da 43 caracteres ASCII: debajo del límite de 72 bytes de bcrypt.
    contrasena = secrets.token_urlsafe(32).encode()
    return bcrypt.hashpw(contrasena, bcrypt.gensalt(rounds=costo)).decode()
