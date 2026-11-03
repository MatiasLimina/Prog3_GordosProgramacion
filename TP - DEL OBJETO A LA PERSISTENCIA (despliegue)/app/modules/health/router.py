import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.health.schemas import LiveRead, ReadyRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=LiveRead, status_code=200)
async def live() -> LiveRead:
    """El proceso está vivo. No toca la base."""
    return LiveRead(estado="vivo")


@router.get("/ready", response_model=ReadyRead, status_code=200)
async def ready(session: AsyncSession = Depends(get_session)) -> ReadyRead:
    """La app puede atender: verifica la conexión con SELECT 1."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        # El detalle va al log del servidor, nunca al cliente.
        logger.exception("Falló la verificación de la base de datos")
        raise HTTPException(status_code=503, detail="La base de datos no está disponible.") from None
    return ReadyRead(estado="listo", base_de_datos="disponible")
