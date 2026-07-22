import speech_recognition as sr
import time
import sys
import os
import glob
from pydub import AudioSegment

def convertir_a_wav(ruta_m4a):
    ruta_wav = ruta_m4a.rsplit('.', 1)[0] + '_temp.wav'
    audio = AudioSegment.from_file(ruta_m4a)
    audio.export(ruta_wav, format='wav')
    return ruta_wav

def transcribir_google(recognizer, ruta_audio):
    ruta_wav = convertir_a_wav(ruta_audio)
    try:
        with sr.AudioFile(ruta_wav) as source:
            audio_data = recognizer.record(source)

        inicio = time.time()
        try:
            texto = recognizer.recognize_google(audio_data, language="es-ES")
        except sr.UnknownValueError:
            texto = "[No se pudo entender el audio]"
        except sr.RequestError as e:
            texto = f"[Error de conexion con Google: {e}]"
        fin = time.time()

        return fin - inicio, texto
    finally:
        if os.path.exists(ruta_wav):
            os.remove(ruta_wav)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python probar_google_speech.py <carpeta_con_audios>")
        sys.exit(1)

    carpeta = sys.argv[1]
    recognizer = sr.Recognizer()

    archivos = sorted(glob.glob(os.path.join(carpeta, "*.m4a")))
    if not archivos:
        print(f"No se encontraron archivos .m4a en: {carpeta}")
        sys.exit(1)

    print(f"{len(archivos)} audios encontrados en la carpeta.\n")

    resultados = []
    for archivo in archivos:
        nombre = os.path.basename(archivo)
        print(f"Transcribiendo: {nombre}")
        tiempo, texto = transcribir_google(recognizer, archivo)
        print(f"Tiempo: {tiempo:.2f} segundos")
        print(f"Texto: {texto}\n")
        resultados.append((nombre, tiempo, texto))

    print("RESUMEN")
    print("="*50)
    tiempo_total = sum(r[1] for r in resultados)
    for nombre, tiempo, texto in resultados:
        print(f"{nombre}: {tiempo:.2f}s -> {texto[:60]}...")
    print(f"\nTiempo medio por audio: {tiempo_total/len(resultados):.2f} segundos")
