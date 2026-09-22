from fastapi import APIRouter, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
import asyncio
import time
from models.order_schemas import OrderCreate, OrderResponse, DemoResponse
from models.common_schemas import ErrorResponse
from repositories.product_repository import ProductRepository
from repositories.client_repository import ClientRepository
from dependencies import get_product_repository, get_client_repository

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

async def _notify_order_confirmed(order_id: int):
    """Tarea en segundo plano para notificar que un pedido fue confirmado."""
    await asyncio.sleep(1) # Simula envío de notificación
    print(f"[BACKGROUND] Notificación enviada para el pedido {order_id}")

@router.post("", response_model=OrderResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def create_order(
    order: OrderCreate,
    background_tasks: BackgroundTasks,
    product_repo: ProductRepository = Depends(get_product_repository),
    client_repo: ClientRepository = Depends(get_client_repository)
):
    # R3.11: Verificación de cliente y stock disponible corren de forma concurrente
    client_exists_task = asyncio.create_task(client_repo.client_exists(order.client_id))
    product_task = asyncio.create_task(product_repo.get_by_id(order.product_id))

    client_exists, product = await asyncio.gather(client_exists_task, product_task)

    if not client_exists:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "CLIENT_NOT_FOUND", "message": f"El cliente con id {order.client_id} no es válido."}}
        )
    
    if not product:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "PRODUCT_NOT_FOUND", "message": f"El producto con id {order.product_id} no existe."}}
        )

    # R3.12: La resta de stock queda protegida contra condiciones de carrera en el repositorio
    success = await product_repo.deduct_stock(order.product_id, order.quantity)
    if not success:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INSUFFICIENT_STOCK", "message": "Stock insuficiente o producto agotado."}}
        )

    order_id = int(time.time() * 1000)
    
    # R3.13: Notificación como tarea en segundo plano usando BackgroundTasks
    background_tasks.add_task(_notify_order_confirmed, order_id)

    return OrderResponse(
        order_id=order_id,
        client_id=order.client_id,
        product_id=order.product_id,
        quantity=order.quantity,
        status="CONFIRMED"
    )

async def _simulated_client_check():
    await asyncio.sleep(1)
    return True

async def _simulated_stock_check():
    await asyncio.sleep(1)
    return True

@router.get("/demo/secuencial", response_model=DemoResponse)
async def demo_sequential():
    start = time.perf_counter()
    
    # Ejecución secuencial
    client_ok = await _simulated_client_check()
    stock_ok = await _simulated_stock_check()
    
    end = time.perf_counter()
    
    return DemoResponse(
        mode="secuencial",
        execution_time_seconds=round(end - start, 4),
        result={"client_ok": client_ok, "stock_ok": stock_ok}
    )

@router.get("/demo/concurrente", response_model=DemoResponse)
async def demo_concurrent():
    start = time.perf_counter()
    
    # Ejecución concurrente usando TaskGroup de asyncio (disponible desde Python 3.11)
    # R3.14: Endpoint para demostrar tiempos de respuesta
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(_simulated_client_check())
        t2 = tg.create_task(_simulated_stock_check())
        
    client_ok = t1.result()
    stock_ok = t2.result()
    
    end = time.perf_counter()
    
    return DemoResponse(
        mode="concurrente",
        execution_time_seconds=round(end - start, 4),
        result={"client_ok": client_ok, "stock_ok": stock_ok}
    )
