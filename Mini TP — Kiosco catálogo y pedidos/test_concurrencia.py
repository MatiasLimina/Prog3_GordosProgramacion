# Puede guardar esto temporalmente como test_concurrencia.py y ejecutarlo con "python test_concurrencia.py"
import asyncio
import httpx
import time

async def hacer_pedido(cliente, producto, cantidad):
    async with httpx.AsyncClient() as client:
        respuesta = await client.post(
            "http://127.0.0.1:8000/pedidos",
            json={"client_id": cliente, "product_id": producto, "quantity": cantidad}
        )
        return respuesta.status_code

async def main():
    print("Enviando 5 pedidos simultáneos...")
    
    # Lanzamos 5 peticiones exactamente al mismo tiempo
    tareas = [hacer_pedido(10, 2, 15) for _ in range(5)]
    resultados = await asyncio.gather(*tareas)
    
    aprobados = resultados.count(200)
    rechazados = resultados.count(400)
    
    print(f"Pedidos aprobados (HTTP 200): {aprobados}")
    print(f"Pedidos rechazados por falta de stock (HTTP 400): {rechazados}")
    print("---")
    print("Si la protección contra condiciones de carrera funciona, sólo 3 pedidos deberían aprobarse (3 x 15 = 45 de stock consumido), y 2 deben ser rechazados.")

if __name__ == "__main__":
    asyncio.run(main())