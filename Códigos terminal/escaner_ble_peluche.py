import asyncio
from bleak import BleakScanner

async def run():
    print("Buscando al Peluche_Inteligente...")
    devices = await BleakScanner.discover()
    encontrado = False
    for d in devices:
        # Buscamos por nombre
        if d.name == "Peluche_Inteligente":
            print(f"\n encontrado")
            print(f"Nombre: {d.name}")
            print(f"Dirección MAC: {d.address}")
            print("-" * 30)
            encontrado = True
    
    if not encontrado:
        print("\nNo se ha encontrado nada.")

asyncio.run(run())    
