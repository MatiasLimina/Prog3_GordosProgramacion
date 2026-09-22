from fastapi import FastAPI
from contextlib import asynccontextmanager
from routers import products, orders
from repositories.product_repository import ProductRepository
from repositories.client_repository import ClientRepository

@asynccontextmanager
async def lifespan(app: FastAPI):
    # R1.4: El recurso compartido se crea una sola vez, en el lifespan de la app
    app.state.product_repo = ProductRepository()
    app.state.client_repo = ClientRepository()
    
    # Inicialización con datos de prueba
    from models.product_schemas import ProductCreate
    from decimal import Decimal
    await app.state.product_repo.create(ProductCreate(name="Alfajor Triple", price=Decimal("1500.50"), stock=100, reserved_stock=10))
    await app.state.product_repo.create(ProductCreate(name="Gaseosa Cola 500ml", price=Decimal("2000.00"), stock=50, reserved_stock=0))
    
    yield
    # Lógica de apagado (si fuera necesaria)

app = FastAPI(title="Kiosco API", lifespan=lifespan)

app.include_router(products.router)
app.include_router(orders.router)

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API del Kiosco Catálogo y Pedidos"}
