import asyncio
from bleak import BleakClient

MAC_ADDRESS = "8C:94:DF:6E:11:56"  
UUID_LUCES = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
UUID_PRESION = "d27038e2-6302-421b-851f-506e7a27572d"

async def main():
    print(f"Intentando conectar con el Peluche ({MAC_ADDRESS})...")
    try:
        # CORREGIDO: Usamos MAC_ADDRESS en lugar de address
        async with BleakClient(MAC_ADDRESS, timeout=20.0) as client:
            print(" ¡CONECTADO CON ÉXITO!")
            
            while True:
                print("\n--- MENÚ DE CONTROL DEL PELUCHE ---")
                print("1: Cambiar a TRISTEZA (Amarillo pastel)")
                print("2: Cambiar a ALEGRÍA (Verde)")
                print("4: Cambiar a ENFADO (Violeta pastel)")
                print("0: Apagar luces (Neutral)")
                print("3: Leer Sensor de Presión")
                print("q: Salir")
                
                opcion = input("Elige una opción: ")

                if opcion == '1':
                    await client.write_gatt_char(UUID_LUCES, b"1")
                    print(">> Comando Tristeza enviado")
                elif opcion == '2':
                    await client.write_gatt_char(UUID_LUCES, b"2")
                    print(">> Comando Alegría enviado")
                elif opcion == '4':
                    await client.write_gatt_char(UUID_LUCES, b"4")
                    print(">> Comando Enfado enviado")
                elif opcion == '0':
                    await client.write_gatt_char(UUID_LUCES, b"0")
                    print(">> Comando Apagar luces enviado")
                elif opcion == '3':
                    valor = await client.read_gatt_char(UUID_PRESION)
                    print(f"\n[DATO] Presión actual: {valor.decode()}")
                elif opcion == 'q':
                    print("Cerrando conexión...")
                    break
                else:
                    print("Opción no válida")

    except Exception as e:
        print(f" Error de conexión: {e}")

if __name__ == "__main__":
    asyncio.run(main())
