import asyncio

class ClientRepository:
    def __init__(self):
        self._valid_clients = {10, 11, 12}

    async def _simulate_delay(self):
        await asyncio.sleep(0.04)

    async def client_exists(self, client_id: int) -> bool:
        await self._simulate_delay()
        return client_id in self._valid_clients
