import whisper
import time
import sys
import os
import glob

def transcribir_audio(modelo, ruta_audio):
    print(f"\n Transcribiendo: {os.path.basename(ruta_audio)}")
    inicio = time.time()
    resultado = modelo.transcribe(ruta_audio, language="es")
    fin = time.time()
    print(f"Tiempo: {fin - inicio:.2f} segundos")
    print(f"Texto: {resultado['text']}")
    return fin - inicio, resultado["text"]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python probar_whisper_local.py <carpeta_con_audios> [modelo]")
        print("Modelos disponibles: tiny, base, small, medium, large")
        sys.exit(1)

    carpeta = sys.argv[1]
    modelo_nombre = sys.argv[2] if len(sys.argv) > 2 else "base"

    print(f" Cargando modelo Whisper ({modelo_nombre})...")
    modelo = whisper.load_model(modelo_nombre)

    archivos = sorted(glob.glob(os.path.join(carpeta, "*.m4a")))
    if not archivos:
        print(f" No se encontraron archivos .m4a en: {carpeta}")
        sys.exit(1)

    print(f"\n {len(archivos)} audios encontrados en la carpeta.")

    resultados = []
    for archivo in archivos:
        tiempo, texto = transcribir_audio(modelo, archivo)
        resultados.append((os.path.basename(archivo), tiempo, texto))

    print("RESUMEN")
    print("="*50)
    tiempo_total = sum(r[1] for r in resultados)
    for nombre, tiempo, texto in resultados:
        print(f"{nombre}: {tiempo:.2f}s -> {texto[:60]}...")
    print(f"\nTiempo medio por audio: {tiempo_total/len(resultados):.2f} segundos")
