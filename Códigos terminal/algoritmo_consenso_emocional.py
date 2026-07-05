import os
import sys
import logging
import queue
import threading
import asyncio
import numpy as np
import joblib
import warnings
import time
import scipy.io.wavfile as wavfile
import speech_recognition as sr  
from bleak import BleakClient
import sounddevice as sd

# --- CONFIGURACION DE ENLACE BLUETOOTH ---
MAC_ADDRESS = "8C:94:DF:6E:11:56"
UUID_LUCES = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
UUID_PRESION = "d27038e2-6302-421b-851f-506e7a27572d"
UUID_IMU = "cba1d466-344c-4be3-ab3f-189f80dd7518"

NOMBRE_MODELO = 'modelo_svm.pkl'
NOMBRE_ENCODER = 'encoder.pkl'

FS = 44100  
SEGUNDOS_VENTANA = 10
MUESTRAS_TOTALES = FS * SEGUNDOS_VENTANA
buffer_audio = np.zeros(MUESTRAS_TOTALES, dtype=np.float32)

print("INICIANDO SCRIPT CENTRAL")

try:
    modelo_svm = joblib.load(NOMBRE_MODELO)
    le = joblib.load(NOMBRE_ENCODER)
    print("Pilar 2: Modelos cargados con éxito.")
except Exception as e:
    print("Error cargando los archivos pkl del SVM: " + str(e))
    exit()

reconocedor = sr.Recognizer()
print("Pilar 3: Google Nube configurado.")

def pilar3_analisis_texto(texto):
    t = texto.lower()
    # RECUERDA: Cambiar los ["..."] por palabras clave reales de tu estudio
    if any(w in t for w in ["enfadado", "rabia", "no"]): return "ENFADO"
    if any(w in t for w in ["triste", "llorar", "ayuda"]): return "TRISTEZA"
    if any(w in t for w in ["bien", "feliz", "alegre"]): return "ALEGRIA"
    return "NEUTRAL"

def pilar1_analisis_matematico(audio_data):
    energia_promedio = np.mean(np.abs(audio_data)) * 150
    amplitud_maxima = np.max(np.abs(audio_data)) * 150
    variabilidad_energia = np.std(np.abs(audio_data)) * 150
    zcr = np.mean(np.diff(np.sign(audio_data)) != 0)

    if energia_promedio < 0.3: 
        print(f" -> CUMPLIDO: (energia_promedio < 0.3) -> Silencio absoluto.")
        return "SILENCIO"
        
    if 0.3 <= energia_promedio <= 5.5:
        # CORREGIDO: Línea unificada para evitar el SyntaxError
        if (energia_promedio < 4.00 and variabilidad_energia < 12.00) or (variabilidad_energia < 2.00): 
            print(f" -> CONDICION A TRISTEZA")
            return "TRISTEZA"
            
        elif variabilidad_energia >= 12.00 and 0.05 <= zcr <= 0.16:
            print(f" -> CONDICION B LLANTO")
            return "TRISTEZA"
            
        else: 
            print(f"Energia moderada con dinamismo normal -> Evaluado como NEUTRAL.")
            return "NEUTRAL"
            
    if energia_promedio > 5.5:
        if amplitud_maxima > 80.0 and zcr > 0.18: 
            print(f" -> ENFADO.")
            return "ENFADO"
        else: 
            print(f" -> ALEGRIA.")
            return "ALEGRIA"
            
    return "NEUTRAL"

def pilar2_predecir_svm(audio_data):
    rms_mean = np.mean(np.sqrt(np.maximum(audio_data**2, 0)))
    rms_std = np.std(np.sqrt(np.maximum(audio_data**2, 0)))
    zcr_mean = np.mean(np.diff(np.sign(audio_data)) != 0)
    
    if rms_std < 0.002 or rms_mean < 0.003:
        return "NEUTRAL"
        
    f0_mean = f0_std = f0_max = 0.0  
    mfcc_means = [rms_mean * (i+1) * 0.1 for i in range(25)]
    features = np.array([rms_mean, rms_std, zcr_mean, f0_mean, f0_std, f0_max, *mfcc_means]).reshape(1, -1)
    
    try:
        pred_idx = modelo_svm.predict(features)[0]
        return le.classes_[pred_idx].upper()
    except:
        return "NEUTRAL"

# --- ETAPA 1: ALGORITMO DE CONSENSO DE VOZ---
def determinar_emocion_voz(p1, p2, p3):
    if p1 == "SILENCIO": return "NEUTRAL"
    
    ia_emocion = "NEUTRAL"
    if p2 == "POSITIVO" or p2 == "ALEGRIA": ia_emocion = "ALEGRIA"
    elif p2 == "NEGATIVO" or p2 == "TRISTEZA": ia_emocion = "TRISTEZA"
    elif p2 == "ENFADO": ia_emocion = "ENFADO"

    if p1 == ia_emocion: return p1
    if p1 == p3: return p1
    if ia_emocion == p3: return p3

    if p2 == "NEGATIVO" and (p1 == "ENFADO" or p3 == "ENFADO"): return "ENFADO"

    return "NEUTRAL"

def audio_callback(indata, frames, time_info, status):
    global buffer_audio
    buffer_audio = np.roll(buffer_audio, -frames)
    buffer_audio[-frames:] = indata[:, 0]

# --- ETAPA 2: FUSION SENSORIAL FRENTE A RUIDO ---
async def bucle_control(client):
    print("\n(Ventana: 10s).")
    print("Calibrando sensores...")
    await asyncio.sleep(20)
    
    while True:
        t_inicio = time.time()
        print("\nPROCESANDO 10 SEGUNDOS DE AUDIO Y HARDWARE...") 
        
        audio_data = np.copy(buffer_audio[-MUESTRAS_TOTALES:])
        audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=0.0, neginf=0.0)
        
        temp_filename = "temp_chunk.wav"
        
        try:
            texto_transcrito = ""
            wavfile.write(temp_filename, FS, (audio_data * 32767).astype(np.int16))
            
            with sr.AudioFile(temp_filename) as fuente:
                audio_listo = reconocedor.record(fuente)
            try:
                texto_transcrito = reconocedor.recognize_google(audio_listo, language="es-ES").strip()
            except sr.UnknownValueError:
                texto_transcrito = ""  
            except sr.RequestError:
                texto_transcrito = ""  
            
            p1 = pilar1_analisis_matematico(audio_data)
            p2 = pilar2_predecir_svm(audio_data) 
            p3 = pilar3_analisis_texto(texto_transcrito)
            
            emocion_voz = determinar_emocion_voz(p1, p2, p3)
            
            raw_p = await client.read_gatt_char(UUID_PRESION)
            presion_sumada = int(raw_p.decode())
            raw_i = await client.read_gatt_char(UUID_IMU)
            movimiento = float(raw_i.decode())

            UMBRAL_PRESION_ALTA = 2650   
            UMBRAL_MOV_SACUDIDA = 180.0  

            emocion_final_absoluta = "NEUTRAL"
            accion_luces = "0"
            motivo = "Esperando estimulos..."

            # ÁRBOL DE DECISIÓN CORREGIDO (Líneas unificadas)
            if emocion_voz == "ENFADO":
                emocion_final_absoluta = "ENFADO"
                accion_luces = "4"
                motivo = "Voz validada por coincidencia acustica."
                
            elif emocion_voz == "TRISTEZA":
                emocion_final_absoluta = "TRISTEZA"
                accion_luces = "1"
                motivo = "Voz validada por coincidencia acustica."
                
            elif emocion_voz == "ALEGRIA":
                emocion_final_absoluta = "ALEGRIA"
                accion_luces = "2"
                motivo = "Interaccion positiva confirmada por voz."
                
            else:
                if p2 == "NEGATIVO" and movimiento > UMBRAL_MOV_SACUDIDA:
                    emocion_final_absoluta = "ENFADO"
                    accion_luces = "4"
                    motivo = "Filtro acústico negativo y sacudida física."
                    
                elif p2 == "NEGATIVO" and presion_sumada > UMBRAL_PRESION_ALTA and movimiento <= UMBRAL_MOV_SACUDIDA:
                    emocion_final_absoluta = "TRISTEZA"
                    accion_luces = "1"
                    motivo = "Filtro acústico negativo y presión alta."
                
                else:
                    if movimiento > UMBRAL_MOV_SACUDIDA:
                        emocion_final_absoluta = "ENFADO"
                        accion_luces = "4"
                        motivo = "Movimiento brusco detectado."

                    elif presion_sumada > UMBRAL_PRESION_ALTA and movimiento <= UMBRAL_MOV_SACUDIDA:
                        emocion_final_absoluta = "TRISTEZA"
                        accion_luces = "1"
                        motivo = "Filtro fisico: Abrazo fuerte."
                    else:
                        emocion_final_absoluta = "NEUTRAL"
                        accion_luces = "0"
                        motivo = "Reposo general o ausencia de patrones."

            print(f"[GOOGLE NUBE] Transcripcion: \"{texto_transcrito}\"")
            print(f"[VOZ] Diagnostico Pilares -> P1:{p1} | P2:{p2} | P3:{p3} -> VOZ DECIDIDA: {emocion_voz}")
            print(f"Presión: {presion_sumada} | IMU: {movimiento:.2f}")
            print(f"EMOCION FINAL ABSOLUTA: {emocion_final_absoluta} ({motivo})")
            
            await client.write_gatt_char(UUID_LUCES, accion_luces.encode())

        except Exception as e:
            print("Error en bucle de fusion: " + str(e))
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        
        t_procesado = time.time() - t_inicio
        tiempo_espera = max(0.1, 10.0 - t_procesado)
        await asyncio.sleep(tiempo_espera)

def arrancar_bucle_bluetooth(loop, mac):
    asyncio.set_event_loop(loop)
    async def conectar_y_correr():
        print("Buscando y conectando al peluche por BLE: " + mac)
        try:
            async with BleakClient(mac, timeout=20.0) as client:
                if client.is_connected:
                    print("CONEXION BLUETOOTH ESTABLECIDA CON EL PELUCHE.")
                    with sd.InputStream(samplerate=FS, channels=1, callback=audio_callback):
                        await bucle_control(client)
        except Exception as e:
            print("Fallo critico en protocolo Bluetooth: " + str(e))
    loop.run_until_complete(conectar_y_correr())

if __name__ == "__main__":
    nuevo_loop = asyncio.new_event_loop()
    hilo_ble = threading.Thread(target=arrancar_bucle_bluetooth, args=(nuevo_loop, MAC_ADDRESS), daemon=True)
    hilo_ble.start()
    try:
        while True:
            hilo_ble.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\n[CIERRE] Cerrando de forma segura...")
        nuevo_loop.stop()
