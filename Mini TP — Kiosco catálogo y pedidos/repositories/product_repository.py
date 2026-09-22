import asyncio
from typing import Dict, List, Optional
from models.product_schemas import ProductCreate, ProductUpdate, ProductRead

class ProductRepository:
    def __init__(self):
        self._data: Dict[int, ProductRead] = {}
        self._lock = asyncio.Lock()
        self._counter = 1

    async def _simulate_delay(self):
        await asyncio.sleep(0.04)

    async def get_all(self, offset: int = 0, limit: int = 10) -> tuple[List[ProductRead], int]:
        await self._simulate_delay()
        items = list(self._data.values())
        total = len(items)
        return items[offset: offset + limit], total

    async def get_by_id(self, product_id: int) -> Optional[ProductRead]:
        await self._simulate_delay()
        return self._data.get(product_id)

    async def create(self, product_in: ProductCreate) -> ProductRead:
        await self._simulate_delay()
        async with self._lock:
            product = ProductRead(
                id=self._counter,
                name=product_in.name,
                price=product_in.price,
                stock=product_in.stock,
                reserved_stock=product_in.reserved_stock,
            )
            self._data[self._counter] = product
            self._counter += 1
            return product

    async def update(self, product_id: int, product_update: ProductUpdate) -> Optional[ProductRead]:
        await self._simulate_delay()
        async with self._lock:
            if product_id not in self._data:
                return None
            
            existing = self._data[product_id]
            
            # exclude_unset=True permite distinguir entre campos no enviados y campos enviados como null.
            update_data = product_update.model_dump(exclude_unset=True)
            
            new_data = existing.model_dump()
            new_data.update(update_data)
            
            # Validar de nuevo que el stock reservado no supere al stock (regla de negocio cruzada)
            if new_data["reserved_stock"] > new_data["stock"]:
                raise ValueError("El stock reservado no puede superar al stock total tras la actualización.")
            
            updated_product = ProductRead(**new_data)
            self._data[product_id] = updated_product
            return updated_product
            
    async def deduct_stock(self, product_id: int, quantity: int) -> bool:
        await self._simulate_delay()
        async with self._lock:
            product = self._data.get(product_id)
            if not product:
                return False
            available = product.stock - product.reserved_stock
            if available >= quantity:
                # Modificamos el stock directamente
                new_data = product.model_dump()
                new_data["stock"] -= quantity
                self._data[product_id] = ProductRead(**new_data)
                return True
            return False
